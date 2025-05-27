from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import db
from database.models import Ingrediente, Plato, TipoUnidad, platos_ingredientes, Menu
from sqlalchemy import insert
import csv
import io
import os
from datetime import datetime

importar_bp = Blueprint('importar', __name__)

def get_tipo_unidad(unidad_str):
    """Convert string unit to TipoUnidad enum"""
    unidad_str = unidad_str.lower().strip()
    
    # Map common units to our enum
    mapping = {
        'unidades': TipoUnidad.UNIDADES,
        'unidad': TipoUnidad.UNIDADES,
        'u': TipoUnidad.UNIDADES,
        'kg': TipoUnidad.GRAMOS,
        'kilogramos': TipoUnidad.GRAMOS,
        'kilogramo': TipoUnidad.GRAMOS,
        'g': TipoUnidad.GRAMOS,
        'gr': TipoUnidad.GRAMOS,
        'gramos': TipoUnidad.GRAMOS,
        'gramo': TipoUnidad.GRAMOS,
        'l': TipoUnidad.LITROS,
        'lt': TipoUnidad.LITROS,
        'litros': TipoUnidad.LITROS,
        'litro': TipoUnidad.LITROS,
        'ml': TipoUnidad.MILILITROS,
        'mililitros': TipoUnidad.MILILITROS,
        'mililitro': TipoUnidad.MILILITROS,
    }
    
    return mapping.get(unidad_str, TipoUnidad.UNIDADES)

def convert_quantity(cantidad, unidad_origen, unidad_destino):
    """Convert quantities between units"""
    # If units are the same, no conversion needed
    if unidad_origen == unidad_destino:
        return cantidad
    
    # Convert kg to g
    if unidad_origen == 'kg' and unidad_destino == TipoUnidad.GRAMOS:
        return cantidad * 1000
    
    # Convert l to ml
    if unidad_origen == 'l' and unidad_destino == TipoUnidad.MILILITROS:
        return cantidad * 1000
    
    # Return original if no conversion rule found
    return cantidad

@importar_bp.route('/')
def index():
    """Show import options"""
    return render_template('importar/index.html')

@importar_bp.route('/platos', methods=['GET', 'POST'])
def importar_platos():
    """Import dishes from CSV file"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        if file and file.filename.endswith('.csv'):
            # Get dish name from filename (without extension)
            nombre_plato = os.path.splitext(file.filename)[0]
            
            # Read CSV content
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.DictReader(stream)
            
            ingredientes_data = []
            for row in csv_reader:
                ingrediente_nombre = row.get('Líneas de la lista de materiales', '').strip()
                cantidad_str = row.get('Líneas de la lista de materiales/Cantidad', '0').strip()
                unidad_str = row.get('Líneas de la lista de materiales/Unidad de medida del producto', 'unidades').strip()
                
                if ingrediente_nombre:
                    try:
                        cantidad = float(cantidad_str.replace(',', '.'))
                    except ValueError:
                        cantidad = 0
                    
                    ingredientes_data.append({
                        'nombre': ingrediente_nombre,
                        'cantidad': cantidad,
                        'unidad_original': unidad_str,
                        'tipo_unidad': get_tipo_unidad(unidad_str).value  # Convert enum to string
                    })
            
            # Store data in session for preview
            session['import_data'] = {
                'nombre_plato': nombre_plato,
                'ingredientes': ingredientes_data
            }
            
            return redirect(url_for('importar.preview_platos'))
        else:
            flash('Por favor, seleccione un archivo CSV', 'danger')
            return redirect(request.url)
    
    return render_template('importar/platos.html')

@importar_bp.route('/platos/preview', methods=['GET', 'POST'])
def preview_platos():
    """Preview and edit import data before confirmation"""
    if 'import_data' not in session:
        flash('No hay datos para importar', 'danger')
        return redirect(url_for('importar.importar_platos'))
    
    import_data = session['import_data']
    
    if request.method == 'POST':
        # Get form data
        nombre_plato = request.form.get('nombre_plato')
        lote_plato = request.form.get('lote_plato', '')
        stock_inicial = float(request.form.get('stock_inicial', 0))
        unidad_plato = request.form.get('unidad_plato', 'unidades')
        
        # Get ingredient data
        ingredientes_nombres = request.form.getlist('ingrediente_nombre[]')
        ingredientes_cantidades = request.form.getlist('ingrediente_cantidad[]')
        ingredientes_unidades = request.form.getlist('ingrediente_unidad[]')
        ingredientes_lotes = request.form.getlist('ingrediente_lote[]')
        ingredientes_stocks = request.form.getlist('ingrediente_stock[]')
        ingredientes_caducidades = request.form.getlist('ingrediente_caducidad[]')
        
        try:
            # Check if dish already exists
            plato_existente = Plato.query.filter_by(nombre=nombre_plato).first()
            if plato_existente:
                flash(f'El plato "{nombre_plato}" ya existe', 'warning')
                return redirect(request.url)
            
            # Create dish
            plato = Plato(
                nombre=nombre_plato,
                lote_propio=lote_plato,
                stock_actual=stock_inicial,
                unidad=unidad_plato
            )
            db.session.add(plato)
            db.session.flush()
            
            # Process ingredients
            created_ingredients = 0
            for i in range(len(ingredientes_nombres)):
                nombre = ingredientes_nombres[i].strip()
                if not nombre:
                    continue
                
                cantidad = float(ingredientes_cantidades[i].replace(',', '.'))
                unidad = ingredientes_unidades[i]
                lote = ingredientes_lotes[i]
                stock = float(ingredientes_stocks[i].replace(',', '.')) if ingredientes_stocks[i] else 0
                caducidad = ingredientes_caducidades[i] if ingredientes_caducidades[i] else None
                
                # Check if ingredient exists
                ingrediente = Ingrediente.query.filter_by(nombre=nombre).first()
                
                if not ingrediente:
                    # Create new ingredient
                    tipo_unidad = get_tipo_unidad(unidad)
                    ingrediente = Ingrediente(
                        nombre=nombre,
                        tipo_unidad=tipo_unidad,
                        stock_actual=stock,
                        lote=lote if lote else None,
                        fecha_caducidad=datetime.strptime(caducidad, '%Y-%m-%d').date() if caducidad else None
                    )
                    db.session.add(ingrediente)
                    db.session.flush()
                    created_ingredients += 1
                
                # Add ingredient to dish
                # Convert quantity if necessary
                cantidad_convertida = convert_quantity(cantidad, unidad, ingrediente.tipo_unidad)
                
                stmt = insert(platos_ingredientes).values(
                    plato_id=plato.id,
                    ingrediente_id=ingrediente.id,
                    cantidad=cantidad_convertida,
                    unidad=ingrediente.tipo_unidad.value
                )
                db.session.execute(stmt)
            
            db.session.commit()
            
            # Clear session data
            session.pop('import_data', None)
            
            flash(f'Plato "{nombre_plato}" creado exitosamente con {len(ingredientes_nombres)} ingredientes ({created_ingredients} nuevos)', 'success')
            return redirect(url_for('platos.listar'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al importar: {str(e)}', 'danger')
            return redirect(request.url)
    
    # Check existing ingredients
    for ing in import_data['ingredientes']:
        existing = Ingrediente.query.filter_by(nombre=ing['nombre']).first()
        ing['exists'] = existing is not None
        ing['existing_data'] = existing if existing else None
    
    # Check if dish exists
    plato_exists = Plato.query.filter_by(nombre=import_data['nombre_plato']).first() is not None
    
    return render_template('importar/preview_platos.html', 
                         import_data=import_data,
                         plato_exists=plato_exists)

@importar_bp.route('/platos/cancel')
def cancel_import():
    """Cancel import and clear session data"""
    session.pop('import_data', None)
    flash('Importación cancelada', 'info')
    return redirect(url_for('importar.importar_platos'))

@importar_bp.route('/inventario', methods=['GET', 'POST'])
def importar_inventario():
    """Import dishes from inventory CSV file (simple format with just dish names)"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        if file and file.filename.endswith('.csv'):
            try:
                # Read CSV content
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(stream)
                
                platos_creados = 0
                platos_existentes = 0
                
                for row in csv_reader:
                    nombre_plato = row.get('Nombre', '').strip()
                    if nombre_plato and nombre_plato.strip('"'):
                        # Remove quotes from name
                        nombre_plato = nombre_plato.strip('"')
                        
                        # Check if dish already exists
                        plato_existente = Plato.query.filter_by(nombre=nombre_plato).first()
                        if plato_existente:
                            platos_existentes += 1
                        else:
                            # Create new dish with default values
                            plato = Plato(
                                nombre=nombre_plato,
                                stock_actual=0,
                                unidad='unidades'
                            )
                            db.session.add(plato)
                            platos_creados += 1
                
                db.session.commit()
                
                if platos_creados > 0:
                    flash(f'Se crearon {platos_creados} platos nuevos', 'success')
                if platos_existentes > 0:
                    flash(f'{platos_existentes} platos ya existían y no se modificaron', 'info')
                
                return redirect(url_for('platos.listar'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error al importar: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Por favor, seleccione un archivo CSV', 'danger')
            return redirect(request.url)
    
    return render_template('importar/inventario.html')

@importar_bp.route('/tipos-menu', methods=['GET', 'POST'])
def importar_tipos_menu():
    """Import menu types from CSV file and create menus for each week and day"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        tipo_comida = request.form.get('tipo_comida', 'almuerzo')
        
        if file and file.filename.endswith('.csv'):
            try:
                # Read CSV content
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.DictReader(stream)
                
                menus_creados = 0
                menus_existentes = 0
                errores = []
                
                # Get enum values
                from database.models import DiaSemana, TipoComida
                dias_semana = [
                    DiaSemana.LUNES,
                    DiaSemana.MARTES,
                    DiaSemana.MIERCOLES,
                    DiaSemana.JUEVES,
                    DiaSemana.VIERNES,
                    DiaSemana.SABADO,
                    DiaSemana.DOMINGO
                ]
                
                tipo_comida_enum = TipoComida[tipo_comida.upper()]
                
                for row in csv_reader:
                    tipo_menu = row.get('Valores', '').strip()
                    if not tipo_menu:
                        continue
                    
                    # Create menus for each week (1-4) and day of the week
                    for num_semana in range(1, 5):  # Weeks 1-4
                        for dia_semana in dias_semana:
                            # Create menu name
                            nombre_menu = f"{tipo_menu} S{num_semana} {dia_semana.value.title()} {tipo_comida.title()}"
                            
                            # Check if menu already exists
                            menu_existente = Menu.query.filter_by(
                                nombre=nombre_menu,
                                dia_semana=dia_semana,
                                numero_semana=num_semana,
                                tipo_comida=tipo_comida_enum,
                                tipo_dieta=tipo_menu
                            ).first()
                            
                            if menu_existente:
                                menus_existentes += 1
                            else:
                                # Create new menu
                                menu = Menu(
                                    nombre=nombre_menu,
                                    dia_semana=dia_semana,
                                    numero_semana=num_semana,
                                    tipo_dieta=tipo_menu,
                                    tipo_comida=tipo_comida_enum
                                )
                                db.session.add(menu)
                                menus_creados += 1
                
                db.session.commit()
                
                # Show results
                if menus_creados > 0:
                    flash(f'Se crearon {menus_creados} menús nuevos', 'success')
                if menus_existentes > 0:
                    flash(f'{menus_existentes} menús ya existían y no se modificaron', 'info')
                
                return redirect(url_for('menus.listar'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error al importar: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Por favor, seleccione un archivo CSV', 'danger')
            return redirect(request.url)
    
    return render_template('importar/tipos_menu.html')