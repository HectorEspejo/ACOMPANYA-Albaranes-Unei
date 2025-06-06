from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from database import db
from database.models import Ingrediente, Plato, TipoUnidad, platos_ingredientes, Menu, Cliente, Albaran, AlbaranDetalle, TipoComida, DiaSemana, menus_platos
from sqlalchemy import insert
import csv
import io
import os
from datetime import datetime, timedelta
from urllib.parse import unquote

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
@login_required
def index():
    """Show import options"""
    return render_template('importar/index.html')

@importar_bp.route('/platos', methods=['GET', 'POST'])
@login_required
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
@login_required
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
@login_required
def cancel_import():
    """Cancel import and clear session data"""
    session.pop('import_data', None)
    flash('Importación cancelada', 'info')
    return redirect(url_for('importar.importar_platos'))

@importar_bp.route('/inventario', methods=['GET', 'POST'])
@login_required
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
@login_required
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

@importar_bp.route('/requisitos-menu', methods=['GET', 'POST'])
@login_required
def importar_requisitos_menu():
    """Import menu requirements per client from CSV file"""
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
                csv_reader = csv.reader(stream)
                
                # Skip header row if present
                next(csv_reader, None)
                
                requisitos_procesados = 0
                clientes_no_encontrados = []
                menus_no_encontrados = []
                albaranes_actualizados = 0
                
                # Map day columns to DiaSemana enum values
                dias_map = {
                    'L': 'lunes',
                    'M': 'martes',
                    'X': 'miercoles',
                    'J': 'jueves',
                    'V': 'viernes',
                    'S': 'sabado',
                    'D': 'domingo'
                }
                
                # Map meal type keywords to TipoComida
                tipo_comida_map = {
                    'ALMUERZO': TipoComida.ALMUERZO,
                    'CENA': TipoComida.CENA,
                    'DESAYUNO': TipoComida.DESAYUNO,
                    'MERIENDA': TipoComida.MERIENDA
                }
                
                # Get week 1 date range (assuming current week or you can adjust)
                # For now, we'll use the first Monday of the current month
                today = datetime.now().date()
                first_day = today.replace(day=1)
                # Find the first Monday
                days_until_monday = (7 - first_day.weekday()) % 7
                if days_until_monday == 0 and first_day.weekday() != 0:
                    days_until_monday = 7
                week1_start = first_day + timedelta(days=days_until_monday)
                
                for row in csv_reader:
                    if len(row) < 9:  # Need at least 9 columns (A-I)
                        continue
                    
                    cliente_nombre = row[0].strip()
                    menu_type_raw = row[1].strip()
                    
                    if not cliente_nombre or not menu_type_raw:
                        continue
                    
                    # Find client by partial name match
                    cliente = Cliente.query.filter(
                        Cliente.nombre.contains(cliente_nombre)
                    ).first()
                    
                    if not cliente:
                        clientes_no_encontrados.append(cliente_nombre)
                        continue
                    
                    # Parse menu type and meal type
                    tipo_dieta = None
                    tipo_comida = None
                    
                    # Extract meal type
                    for keyword, comida_enum in tipo_comida_map.items():
                        if keyword in menu_type_raw.upper():
                            tipo_comida = comida_enum
                            break
                    
                    # Parse diet type - extract the base type
                    menu_upper = menu_type_raw.upper()
                    if 'BASAL' in menu_upper:
                        tipo_dieta = 'BASAL'
                    elif 'DIABETICO SIN SAL' in menu_upper or 'DIABÉTICO SIN SAL' in menu_upper:
                        tipo_dieta = 'DIABETICO SIN SAL'
                    elif 'DIABETICO' in menu_upper or 'DIABÉTICO' in menu_upper:
                        tipo_dieta = 'DIABETICO'
                    elif 'HIPOCALORICO' in menu_upper or 'HIPOCALÓRICO' in menu_upper:
                        tipo_dieta = 'HIPOCALORICO'
                    elif 'SIN SAL' in menu_upper:
                        tipo_dieta = 'SIN SAL'
                    elif 'TURMIX' in menu_upper:
                        tipo_dieta = 'TURMIX'
                    else:
                        # Try to get the first word as diet type
                        parts = menu_type_raw.split()
                        if parts:
                            tipo_dieta = parts[0].upper()
                    
                    if not tipo_comida:
                        # Default to almuerzo if not specified
                        tipo_comida = TipoComida.ALMUERZO
                    
                    # Process each day (columns C-I)
                    for i, day_letter in enumerate(['L', 'M', 'X', 'J', 'V', 'S', 'D']):
                        column_index = i + 2  # Starting from column C (index 2)
                        if column_index >= len(row):
                            continue
                        
                        cantidad_str = row[column_index].strip()
                        if not cantidad_str or cantidad_str == '0':
                            continue
                        
                        try:
                            cantidad = int(cantidad_str)
                        except ValueError:
                            continue
                        
                        # Find the menu for week 1, this day, diet type and meal type
                        dia_semana = dias_map[day_letter]
                        
                        # Convert string to DiaSemana enum
                        from database.models import DiaSemana as DS
                        dia_semana_enum = DS[dia_semana.upper()]
                        
                        menu = Menu.query.filter_by(
                            numero_semana=1,
                            dia_semana=dia_semana_enum,
                            tipo_dieta=tipo_dieta,
                            tipo_comida=tipo_comida
                        ).first()
                        
                        if not menu:
                            menus_no_encontrados.append(f"{tipo_dieta} {tipo_comida.value} S1 {dia_semana}")
                            continue
                        
                        # Calculate the date for this day in week 1
                        day_offset = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'].index(dia_semana)
                        fecha_albaran = week1_start + timedelta(days=day_offset)
                        
                        # Find or create albaran for this client and date
                        albaran = Albaran.query.filter_by(
                            cliente_id=cliente.id,
                            fecha=fecha_albaran
                        ).first()
                        
                        if not albaran:
                            # Create new albaran
                            albaran = Albaran(
                                referencia=Albaran.generar_referencia(),
                                cliente_id=cliente.id,
                                destinatario=cliente.nombre,
                                fecha=fecha_albaran
                            )
                            db.session.add(albaran)
                            db.session.flush()
                        
                        # Check if this menu is already in the albaran
                        existing_detail = AlbaranDetalle.query.filter_by(
                            albaran_id=albaran.id,
                            menu_id=menu.id
                        ).first()
                        
                        if existing_detail:
                            # Update quantity (we'll update the quantity for all related dishes)
                            # First, remove old details for this menu
                            AlbaranDetalle.query.filter_by(
                                albaran_id=albaran.id,
                                menu_id=menu.id
                            ).delete()
                        
                        # Add menu dishes to albaran with the specified quantity
                        for plato, cantidad_plato in menu.obtener_platos_con_cantidad():
                            lotes = ', '.join(plato.obtener_lotes_trazabilidad())
                            
                            detalle = AlbaranDetalle(
                                albaran_id=albaran.id,
                                menu_id=menu.id,
                                plato_id=plato.id,
                                cantidad_entregada=cantidad_plato * cantidad,
                                unidad=plato.unidad,
                                lote=lotes
                            )
                            db.session.add(detalle)
                        
                        albaranes_actualizados += 1
                        requisitos_procesados += 1
                
                db.session.commit()
                
                # Show results
                flash(f'Se procesaron {requisitos_procesados} requisitos de menú', 'success')
                flash(f'Se actualizaron {albaranes_actualizados} albaranes', 'info')
                
                if clientes_no_encontrados:
                    flash(f'Clientes no encontrados: {", ".join(set(clientes_no_encontrados))}', 'warning')
                
                if menus_no_encontrados:
                    flash(f'Menús no encontrados: {", ".join(set(menus_no_encontrados)[:5])}...', 'warning')
                
                return redirect(url_for('albaranes.listar'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error al importar: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Por favor, seleccione un archivo CSV', 'danger')
            return redirect(request.url)
    
    return render_template('importar/requisitos_menu.html')

@importar_bp.route('/menus', methods=['GET'])
@login_required
def menus():
    """Show menu import form"""
    return render_template('importar/menus.html')

@importar_bp.route('/menus/upload', methods=['POST'])
@login_required
def upload_menus():
    """Process menu CSV file and show preview"""
    if 'file' not in request.files:
        flash('No se seleccionó ningún archivo', 'danger')
        return redirect(url_for('importar.menus'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No se seleccionó ningún archivo', 'danger')
        return redirect(url_for('importar.menus'))
    
    semana = request.form.get('semana')
    dia = request.form.get('dia')
    comida = request.form.get('comida')
    
    if not all([semana, dia, comida]):
        flash('Por favor complete todos los campos', 'danger')
        return redirect(url_for('importar.menus'))
    
    if file and file.filename.endswith('.csv'):
        try:
            # Read CSV content
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_reader = csv.reader(stream)
            
            # Read header to identify column positions
            header = next(csv_reader)
            col_indices = {}
            comida_indices = []
            elemento_indices = []
            
            # Check if this is a breakfast/snack format
            is_elementos_format = comida.upper() in ['DESAYUNO', 'MERIENDA']
            
            for i, col in enumerate(header):
                col_upper = col.upper().strip()
                if col_upper == 'MENÚ':
                    col_indices['menu'] = i
                elif is_elementos_format and col_upper.startswith('ELEMENTO'):
                    elemento_indices.append(i)
                elif col_upper == 'COMIDA' or col_upper == 'COMIDA 1' or col_upper == 'COMIDA 2':
                    comida_indices.append(i)
                    # Store specific indices for new format
                    if col_upper == 'COMIDA 1':
                        col_indices['comida1'] = i
                    elif col_upper == 'COMIDA 2':
                        col_indices['comida2'] = i
                elif col_upper == 'TIPO DE PAN':
                    col_indices['pan'] = i
                elif col_upper == 'POSTRE':
                    col_indices['postre'] = i
            
            menus = []
            platos_unicos = {
                'primeros': {},
                'segundos': {},
                'panes': {},
                'postres': {}
            }
            referencias_sugeridas = {}
            
            # Add elementos category for breakfast/snack
            if is_elementos_format:
                platos_unicos['elementos'] = {}
            
            # Process menu rows
            for row in csv_reader:
                if not row or len(row) < len(header):
                    continue
                
                tipo_menu = row[col_indices.get('menu', 0)].strip() if col_indices.get('menu', 0) < len(row) else ''
                
                # Skip empty rows or rows without menu type
                if not tipo_menu or not tipo_menu.strip():
                    continue
                
                if is_elementos_format:
                    # Process breakfast/snack format
                    elementos = []
                    for idx in elemento_indices:
                        if idx < len(row):
                            elemento = row[idx].strip()
                            if elemento:
                                elementos.append(elemento)
                                # Track unique elements
                                if elemento not in platos_unicos['elementos']:
                                    platos_unicos['elementos'][elemento] = {'count': 0, 'menus': []}
                                platos_unicos['elementos'][elemento]['count'] += 1
                                platos_unicos['elementos'][elemento]['menus'].append(tipo_menu)
                    
                    # Skip if no elements
                    if not elementos:
                        continue
                    
                    menus.append({
                        'tipo_menu': tipo_menu,
                        'elementos': elementos,
                        'cantidad': 0,
                        # Add empty fields for compatibility
                        'primer_plato': '',
                        'segundo_plato': '',
                        'tipo_pan': '',
                        'postre': ''
                    })
                else:
                    # Process lunch/dinner format
                    primer_plato = row[comida_indices[0]].strip() if len(comida_indices) > 0 and comida_indices[0] < len(row) else ''
                    segundo_plato = row[comida_indices[1]].strip() if len(comida_indices) > 1 and comida_indices[1] < len(row) else ''
                    tipo_pan = row[col_indices.get('pan', 3)].strip() if col_indices.get('pan', 3) < len(row) else ''
                    postre = row[col_indices.get('postre', 4)].strip() if col_indices.get('postre', 4) < len(row) else ''
                    
                    # Skip rows without any dishes
                    if not primer_plato and not segundo_plato and not tipo_pan and not postre:
                        continue
                    
                    # Track unique dishes by category
                    if primer_plato:
                        if primer_plato not in platos_unicos['primeros']:
                            platos_unicos['primeros'][primer_plato] = {'count': 0, 'menus': []}
                        platos_unicos['primeros'][primer_plato]['count'] += 1
                        platos_unicos['primeros'][primer_plato]['menus'].append(tipo_menu)
                    
                    if segundo_plato:
                        if segundo_plato not in platos_unicos['segundos']:
                            platos_unicos['segundos'][segundo_plato] = {'count': 0, 'menus': []}
                        platos_unicos['segundos'][segundo_plato]['count'] += 1
                        platos_unicos['segundos'][segundo_plato]['menus'].append(tipo_menu)
                        
                    
                    if tipo_pan:
                        if tipo_pan not in platos_unicos['panes']:
                            platos_unicos['panes'][tipo_pan] = {'count': 0, 'menus': []}
                        platos_unicos['panes'][tipo_pan]['count'] += 1
                        platos_unicos['panes'][tipo_pan]['menus'].append(tipo_menu)
                    
                    if postre:
                        if postre not in platos_unicos['postres']:
                            platos_unicos['postres'][postre] = {'count': 0, 'menus': []}
                        platos_unicos['postres'][postre]['count'] += 1
                        platos_unicos['postres'][postre]['menus'].append(tipo_menu)
                    
                    menus.append({
                        'tipo_menu': tipo_menu,
                        'primer_plato': primer_plato,
                        'segundo_plato': segundo_plato,
                        'tipo_pan': tipo_pan,
                        'postre': postre,
                        'cantidad': 0  # Default quantity, will be set from the menu requirements import
                    })
            
            # Generate suggested references for repeated dishes
            ref_counters = {'primeros': 1, 'segundos': 1, 'panes': 1, 'postres': 1, 'elementos': 1}
            prefijos = {'primeros': 'REF-', 'segundos': 'REF-', 'panes': 'PAN-', 'postres': 'POS-', 'elementos': 'ELEM-'}
            
            for categoria, platos in platos_unicos.items():
                for plato, info in platos.items():
                    if info['count'] > 1:
                        prefijo = prefijos[categoria]
                        referencias_sugeridas[plato] = f'{prefijo}{str(ref_counters[categoria]).zfill(3)}'
                        ref_counters[categoria] += 1
            
            # Debug summary
            print("\n=== IMPORT SUMMARY ===")
            print(f"Total menus found: {len(menus)}")
            print(f"Unique first dishes: {len(platos_unicos['primeros'])}")
            print(f"Unique second dishes: {len(platos_unicos['segundos'])}")
            
            # Debug CAZUELA DE BACALAO specifically
            cazuela_count = 0
            cazuela_menus = []
            for menu in menus:
                if 'CAZUELA DE BACALAO' in menu.get('segundo_plato', ''):
                    cazuela_count += 1
                    cazuela_menus.append(menu['tipo_menu'])
            
            print(f"\nCAZUELA DE BACALAO found in {cazuela_count} menus:")
            for m in cazuela_menus[:10]:  # Show first 10
                print(f"  - {m}")
            
            # Check if it's in platos_unicos
            for plato_name, info in platos_unicos['segundos'].items():
                if 'CAZUELA' in plato_name and 'BACALAO' in plato_name:
                    print(f"\nFound in platos_unicos: '{plato_name}' - {info['count']} times")
            
            # Store data in session
            session['menus_import'] = {
                'semana': semana,
                'dia': dia,
                'comida': comida,
                'menus': menus
            }
            
            return render_template('importar/menus_preview.html',
                                 semana=semana,
                                 dia=dia,
                                 comida=comida,
                                 menus=menus,
                                 platos_unicos=platos_unicos,
                                 referencias_sugeridas=referencias_sugeridas,
                                 menus_data=str(menus))  # Pass as string for hidden field
            
        except Exception as e:
            flash(f'Error al leer el archivo: {str(e)}', 'danger')
            return redirect(url_for('importar.menus'))
    else:
        flash('Por favor, seleccione un archivo CSV', 'danger')
        return redirect(url_for('importar.menus'))

@importar_bp.route('/menus/confirm', methods=['POST'])
@login_required
def confirm_menus():
    """Confirm and save imported menus"""
    if 'menus_import' not in session:
        flash('No hay datos de menús para importar', 'danger')
        return redirect(url_for('importar.menus'))
    
    import_data = session['menus_import']
    semana = int(import_data['semana'])
    dia = import_data['dia']
    comida = import_data['comida']
    menus = import_data['menus']
    
    # Get references from form - now grouped by dish name
    referencias = {
        'primeros': {},
        'segundos': {},
        'panes': {},
        'postres': {},
        'elementos': {}
    }
    
    # Debug form data
    print("\n=== FORM DEBUG ===")
    print("Form keys related to 'CAZUELA':")
    for key in request.form:
        if 'CAZUELA' in key.upper() or 'BACALAO' in key.upper():
            print(f"  {key} = {request.form.get(key)}")
    
    # Collect all unique references from form
    for key in request.form:
        if key.startswith('ref_primero_'):
            plato_name = unquote(key.replace('ref_primero_', ''))
            referencias['primeros'][plato_name] = request.form.get(key, '')
        elif key.startswith('ref_segundo_'):
            plato_name = unquote(key.replace('ref_segundo_', ''))
            referencias['segundos'][plato_name] = request.form.get(key, '')
            if 'CAZUELA DE BACALAO' in plato_name:
                print(f"\nDEBUG: Found CAZUELA DE BACALAO in form - Name: '{plato_name}', Ref: '{request.form.get(key)}'")
        elif key.startswith('ref_pan_'):
            plato_name = unquote(key.replace('ref_pan_', ''))
            referencias['panes'][plato_name] = request.form.get(key, '')
        elif key.startswith('ref_postre_'):
            plato_name = unquote(key.replace('ref_postre_', ''))
            referencias['postres'][plato_name] = request.form.get(key, '')
        elif key.startswith('ref_elemento_'):
            plato_name = unquote(key.replace('ref_elemento_', ''))
            referencias['elementos'][plato_name] = request.form.get(key, '')
    
    try:
        # Convert to enums
        dia_enum = DiaSemana[dia.upper()]
        comida_enum = TipoComida[comida.upper()]
        
        menus_creados = 0
        platos_creados = 0
        platos_actualizados = 0
        
        # Create separate maps for each type of dish
        platos_por_referencia = {
            'primeros': {},
            'segundos': {},
            'panes': {},
            'postres': {},
            'elementos': {}
        }
        
        # Debug
        print(f"\n=== PROCESSING {len(menus)} MENUS ===")
        cazuela_processed = 0
        
        for i, menu_data in enumerate(menus):
            
            # Debug specific menu
            if 'CAZUELA DE BACALAO' in menu_data.get('segundo_plato', ''):
                print(f"\n[Menu {i}] Processing {menu_data['tipo_menu']} with CAZUELA DE BACALAO")
                print(f"  Raw data: {menu_data}")
            
            # Create or find menu
            nombre_menu = f"{menu_data['tipo_menu']} S{semana} {dia.title()} {comida.title()}"
            
            menu = Menu.query.filter_by(
                nombre=nombre_menu,
                dia_semana=dia_enum,
                numero_semana=semana,
                tipo_comida=comida_enum,
                tipo_dieta=menu_data['tipo_menu']
            ).first()
            
            if not menu:
                menu = Menu(
                    nombre=nombre_menu,
                    dia_semana=dia_enum,
                    numero_semana=semana,
                    tipo_dieta=menu_data['tipo_menu'],
                    tipo_comida=comida_enum
                )
                db.session.add(menu)
                db.session.flush()
                menus_creados += 1
            else:
                # If menu exists, remove all existing dishes first
                db.session.execute(
                    menus_platos.delete().where(menus_platos.c.menu_id == menu.id)
                )
            
            # Process dishes
            platos_menu = []
            
            # Check if this is a breakfast/snack menu
            if 'elementos' in menu_data:
                # Process breakfast/snack elements
                for elemento in menu_data['elementos']:
                    ref_elemento = referencias['elementos'].get(elemento, '')
                    
                    # Check if we already created a dish with this reference
                    if ref_elemento and ref_elemento in platos_por_referencia['elementos']:
                        plato_elemento = platos_por_referencia['elementos'][ref_elemento]
                    else:
                        # Find or create dish by name or reference
                        if ref_elemento:
                            plato_elemento = Plato.query.filter(
                                (Plato.nombre == elemento) | 
                                (Plato.lote_propio == ref_elemento)
                            ).first()
                        else:
                            plato_elemento = Plato.query.filter_by(nombre=elemento).first()
                        
                        if not plato_elemento:
                            plato_elemento = Plato(
                                nombre=elemento,
                                lote_propio=ref_elemento if ref_elemento else None,
                                stock_actual=0,
                                unidad='unidades'
                            )
                            db.session.add(plato_elemento)
                            db.session.flush()
                            platos_creados += 1
                        elif ref_elemento and not plato_elemento.lote_propio:
                            plato_elemento.lote_propio = ref_elemento
                            platos_actualizados += 1
                        
                        if ref_elemento:
                            platos_por_referencia['elementos'][ref_elemento] = plato_elemento
                    
                    platos_menu.append((plato_elemento, 1, 'elemento'))
            
            # First dish (for lunch/dinner)
            elif menu_data.get('primer_plato'):
                ref_primero = referencias['primeros'].get(menu_data['primer_plato'], '')
                
                # Check if we already created a dish with this reference
                if ref_primero and ref_primero in platos_por_referencia['primeros']:
                    plato_primero = platos_por_referencia['primeros'][ref_primero]
                else:
                    # Find or create dish by name or reference
                    if ref_primero:
                        plato_primero = Plato.query.filter(
                            (Plato.nombre == menu_data['primer_plato']) | 
                            (Plato.lote_propio == ref_primero)
                        ).first()
                    else:
                        plato_primero = Plato.query.filter_by(nombre=menu_data['primer_plato']).first()
                    
                    if not plato_primero:
                        plato_primero = Plato(
                            nombre=menu_data['primer_plato'],
                            lote_propio=ref_primero if ref_primero else None,
                            stock_actual=0,
                            unidad='unidades'
                        )
                        db.session.add(plato_primero)
                        db.session.flush()
                        platos_creados += 1
                    elif ref_primero and not plato_primero.lote_propio:
                        plato_primero.lote_propio = ref_primero
                        platos_actualizados += 1
                    
                    if ref_primero:
                        platos_por_referencia['primeros'][ref_primero] = plato_primero
                
                platos_menu.append((plato_primero, 1, 'primero'))
            
            # Second dish
            if menu_data['segundo_plato']:
                ref_segundo = referencias['segundos'].get(menu_data['segundo_plato'], '')
                
                # Debug CAZUELA
                if 'CAZUELA DE BACALAO' in menu_data['segundo_plato']:
                    cazuela_processed += 1
                    print(f"\n[CAZUELA {cazuela_processed}] Processing for menu: {menu_data['tipo_menu']}")
                    print(f"  Dish name: '{menu_data['segundo_plato']}'")
                    print(f"  Reference assigned: '{ref_segundo}'")
                    print(f"  In platos_por_referencia: {ref_segundo in platos_por_referencia['segundos'] if ref_segundo else 'No ref'}")
                
                # Check if we already created a dish with this reference or name
                if ref_segundo and ref_segundo in platos_por_referencia['segundos']:
                    plato_segundo = platos_por_referencia['segundos'][ref_segundo]
                    if 'CAZUELA DE BACALAO' in menu_data['segundo_plato']:
                        print(f"  Found via reference cache: {plato_segundo.nombre} (ID: {plato_segundo.id})")
                    platos_menu.append((plato_segundo, 1, 'segundo'))
                else:
                    # Check if we already created this dish without reference
                    temp_key = f"dish_segundo_{menu_data['segundo_plato']}"
                    if temp_key in platos_por_referencia['segundos']:
                        plato_segundo = platos_por_referencia['segundos'][temp_key]
                        if 'CAZUELA DE BACALAO' in menu_data['segundo_plato']:
                            print(f"  Found via temp cache: {plato_segundo.nombre} (ID: {plato_segundo.id})")
                        platos_menu.append((plato_segundo, 1, 'segundo'))
                    else:
                        # Find or create dish by name or reference
                        if ref_segundo:
                            plato_segundo = Plato.query.filter(
                                (Plato.nombre == menu_data['segundo_plato']) | 
                                (Plato.lote_propio == ref_segundo)
                            ).first()
                        else:
                            plato_segundo = Plato.query.filter_by(nombre=menu_data['segundo_plato']).first()
                        
                        if 'CAZUELA DE BACALAO' in menu_data['segundo_plato']:
                            if plato_segundo:
                                print(f"  Found in DB: {plato_segundo.nombre} (ID: {plato_segundo.id})")
                            else:
                                print(f"  NOT FOUND in DB - will create new")
                        
                        if not plato_segundo:
                            plato_segundo = Plato(
                                nombre=menu_data['segundo_plato'],
                                lote_propio=ref_segundo if ref_segundo else None,
                                stock_actual=0,
                                unidad='unidades'
                            )
                            db.session.add(plato_segundo)
                            db.session.flush()
                            platos_creados += 1
                            if 'CAZUELA DE BACALAO' in menu_data['segundo_plato']:
                                print(f"  Created new dish with ID: {plato_segundo.id}")
                        elif ref_segundo and not plato_segundo.lote_propio:
                            plato_segundo.lote_propio = ref_segundo
                            platos_actualizados += 1
                            if 'CAZUELA DE BACALAO' in menu_data['segundo_plato']:
                                print(f"  Updated existing dish ID: {plato_segundo.id}")
                        
                        if ref_segundo:
                            platos_por_referencia['segundos'][ref_segundo] = plato_segundo
                        else:
                            # For dishes without reference, use name as temporary key to avoid duplicates
                            temp_key = f"dish_segundo_{menu_data['segundo_plato']}"
                            platos_por_referencia['segundos'][temp_key] = plato_segundo
                        
                        platos_menu.append((plato_segundo, 1, 'segundo'))
                
            
            # Bread
            if menu_data.get('tipo_pan'):
                ref_pan = referencias['panes'].get(menu_data['tipo_pan'], '')
                
                # Check if we already created a dish with this reference
                if ref_pan and ref_pan in platos_por_referencia['panes']:
                    plato_pan = platos_por_referencia['panes'][ref_pan]
                else:
                    # Find or create dish by name or reference
                    if ref_pan:
                        plato_pan = Plato.query.filter(
                            (Plato.nombre == menu_data['tipo_pan']) | 
                            (Plato.lote_propio == ref_pan)
                        ).first()
                    else:
                        plato_pan = Plato.query.filter_by(nombre=menu_data['tipo_pan']).first()
                    
                    if not plato_pan:
                        plato_pan = Plato(
                            nombre=menu_data['tipo_pan'],
                            lote_propio=ref_pan if ref_pan else None,
                            stock_actual=0,
                            unidad='unidades'
                        )
                        db.session.add(plato_pan)
                        db.session.flush()
                        platos_creados += 1
                    elif ref_pan and not plato_pan.lote_propio:
                        plato_pan.lote_propio = ref_pan
                        platos_actualizados += 1
                    
                    if ref_pan:
                        platos_por_referencia['panes'][ref_pan] = plato_pan
                
                platos_menu.append((plato_pan, 1, 'pan'))
            
            # Dessert
            if menu_data.get('postre'):
                ref_postre = referencias['postres'].get(menu_data['postre'], '')
                
                # Check if we already created a dish with this reference
                if ref_postre and ref_postre in platos_por_referencia['postres']:
                    plato_postre = platos_por_referencia['postres'][ref_postre]
                else:
                    # Find or create dish by name or reference
                    if ref_postre:
                        plato_postre = Plato.query.filter(
                            (Plato.nombre == menu_data['postre']) | 
                            (Plato.lote_propio == ref_postre)
                        ).first()
                    else:
                        plato_postre = Plato.query.filter_by(nombre=menu_data['postre']).first()
                    
                    if not plato_postre:
                        plato_postre = Plato(
                            nombre=menu_data['postre'],
                            lote_propio=ref_postre if ref_postre else None,
                            stock_actual=0,
                            unidad='unidades'
                        )
                        db.session.add(plato_postre)
                        db.session.flush()
                        platos_creados += 1
                    elif ref_postre and not plato_postre.lote_propio:
                        plato_postre.lote_propio = ref_postre
                        platos_actualizados += 1
                    
                    if ref_postre:
                        platos_por_referencia['postres'][ref_postre] = plato_postre
                
                platos_menu.append((plato_postre, 1, 'postre'))
            
            # Add dishes to menu using the association table
            for plato, cantidad, tipo in platos_menu:
                # Check if the relationship already exists
                existing = db.session.query(menus_platos).filter_by(
                    menu_id=menu.id,
                    plato_id=plato.id
                ).first()
                
                if not existing:
                    # Insert into the association table
                    stmt = insert(menus_platos).values(
                        menu_id=menu.id,
                        plato_id=plato.id,
                        cantidad=cantidad
                    )
                    db.session.execute(stmt)
        
        db.session.commit()
        
        # Debug final summary
        print(f"\n=== FINAL SUMMARY ===")
        print(f"Total CAZUELA DE BACALAO processed: {cazuela_processed}")
        print(f"Menus created: {menus_creados}")
        print(f"Dishes created: {platos_creados}")
        print(f"Dishes updated: {platos_actualizados}")
        
        # Check if CAZUELA DE BACALAO exists in database
        cazuela_db = Plato.query.filter(Plato.nombre.contains('CAZUELA DE BACALAO')).all()
        print(f"\nCAZUELA DE BACALAO in database after import:")
        for c in cazuela_db:
            print(f"  - ID: {c.id}, Name: '{c.nombre}', Ref: '{c.lote_propio}'")
        
        # Clear session data
        session.pop('menus_import', None)
        
        flash(f'Importación completada: {menus_creados} menús creados, {platos_creados} platos nuevos, {platos_actualizados} platos actualizados', 'success')
        return redirect(url_for('menus.listar'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al importar menús: {str(e)}', 'danger')
        return redirect(url_for('importar.menus'))