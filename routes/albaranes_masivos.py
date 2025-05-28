from flask import Blueprint, render_template, request, redirect, url_for, flash
from database import db
from database.models import Cliente, Menu, Albaran, AlbaranDetalle, TipoComida, DiaSemana
import csv
import io
from datetime import datetime, timedelta

albaranes_masivos_bp = Blueprint('albaranes_masivos', __name__)

# Mapeo de tipos de comida desde el CSV
TIPO_COMIDA_MAP = {
    'ALMUERZO': TipoComida.ALMUERZO,
    'CENA': TipoComida.CENA,
    'DESAYUNO': TipoComida.DESAYUNO,
    'MERIENDA': TipoComida.MERIENDA
}

# Mapeo de días
DIAS_MAP = {
    'L': DiaSemana.LUNES,
    'M': DiaSemana.MARTES,
    'X': DiaSemana.MIERCOLES,
    'J': DiaSemana.JUEVES,
    'V': DiaSemana.VIERNES,
    'S': DiaSemana.SABADO,
    'D': DiaSemana.DOMINGO
}

def parse_menu_name(menu_name_csv):
    """
    Parsea el nombre del menú del CSV para extraer tipo de dieta y tipo de comida
    Ejemplo: 'BASAL INDIVIDUAL ALMUERZO' -> ('BASAL INDIVIDUAL', 'ALMUERZO')
    """
    menu_name_csv = menu_name_csv.strip().upper()
    
    # Buscar el tipo de comida al final del nombre
    tipo_comida = None
    tipo_dieta = menu_name_csv
    
    for comida_key in TIPO_COMIDA_MAP.keys():
        if menu_name_csv.endswith(comida_key):
            tipo_comida = comida_key
            # Remover el tipo de comida del nombre para obtener el tipo de dieta
            tipo_dieta = menu_name_csv.replace(comida_key, '').strip()
            break
    
    # Limpiar abreviaciones comunes
    tipo_dieta = tipo_dieta.replace(' OI', '')
    tipo_dieta = tipo_dieta.replace(' GRUPAL', '')
    
    # Normalizar algunos nombres especiales
    if 'DESAYUNO' in tipo_dieta:
        tipo_dieta = tipo_dieta.replace('DESAYUNO ', '').replace('DESAYUNOS ', '')
        if tipo_dieta == 'BASAL':
            tipo_dieta = 'BASAL'
        elif 'DIETA' in tipo_dieta:
            tipo_dieta = 'DIETA'
    
    if 'MERIENDA' in tipo_dieta:
        tipo_dieta = tipo_dieta.replace('MERIENDA ', '').replace('MERIENDAS ', '')
        if tipo_dieta == 'BASAL':
            tipo_dieta = 'BASAL'
        elif 'DIETA' in tipo_dieta:
            tipo_dieta = 'DIETA'
    
    # Casos especiales de nombres largos
    if tipo_dieta == 'DIABETICO, HIPOCALORICO SIN PATATAS':
        tipo_dieta = 'DIABETICO HIPOCALORICO SIN PATATAS'
    
    return tipo_dieta, tipo_comida

def find_menu(tipo_dieta, tipo_comida, numero_semana, dia_semana):
    """
    Busca un menú en la base de datos basándose en los parámetros
    """
    if not tipo_comida:
        return None
    
    tipo_comida_enum = TIPO_COMIDA_MAP.get(tipo_comida)
    if not tipo_comida_enum:
        return None
    
    # Buscar el menú
    menu = Menu.query.filter_by(
        tipo_dieta=tipo_dieta,
        tipo_comida=tipo_comida_enum,
        numero_semana=numero_semana,
        dia_semana=dia_semana
    ).first()
    
    return menu

def get_week_start_date(week_number, base_date=None):
    """
    Obtiene la fecha de inicio (lunes) de una semana específica
    """
    if not base_date:
        # Usar el primer lunes del mes actual
        today = datetime.now().date()
        first_day = today.replace(day=1)
        # Encontrar el primer lunes
        days_until_monday = (7 - first_day.weekday()) % 7
        if days_until_monday == 0 and first_day.weekday() != 0:
            days_until_monday = 7
        first_monday = first_day + timedelta(days=days_until_monday)
    else:
        first_monday = base_date
    
    # Calcular el lunes de la semana específica
    week_start = first_monday + timedelta(weeks=week_number - 1)
    return week_start

@albaranes_masivos_bp.route('/')
def index():
    """Muestra la página principal de generación masiva de albaranes"""
    return render_template('albaranes_masivos/index.html')

@albaranes_masivos_bp.route('/generar', methods=['GET', 'POST'])
def generar():
    """Genera albaranes masivos desde el archivo CSV"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No se seleccionó ningún archivo', 'danger')
            return redirect(request.url)
        
        # Obtener fecha base si se proporciona
        fecha_base_str = request.form.get('fecha_base')
        fecha_base = None
        if fecha_base_str:
            try:
                fecha_base = datetime.strptime(fecha_base_str, '%Y-%m-%d').date()
                # Asegurarse de que sea un lunes
                if fecha_base.weekday() != 0:
                    flash('La fecha base debe ser un lunes', 'warning')
                    fecha_base = fecha_base - timedelta(days=fecha_base.weekday())
            except:
                fecha_base = None
        
        if file and file.filename.endswith('.csv'):
            try:
                # Leer contenido del CSV
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                csv_reader = csv.reader(stream)
                
                # Variables para el procesamiento
                current_client = None
                headers = []
                albaranes_creados = 0
                clientes_procesados = set()
                menus_no_encontrados = set()
                
                for row_num, row in enumerate(csv_reader):
                    # Primera fila contiene los headers con los días
                    if row_num == 0:
                        headers = row
                        continue
                    
                    # Ignorar filas vacías
                    if not any(row):
                        continue
                    
                    # Si la columna A tiene valor y la B está vacía, es un nuevo cliente
                    if row[0] and not row[1]:
                        current_client = row[0].strip().strip('"')
                        continue
                    
                    # Si no hay cliente actual o no hay menú, saltar
                    if not current_client or not row[1]:
                        continue
                    
                    # Procesar línea de menú
                    menu_name_csv = row[1].strip()
                    if not menu_name_csv:
                        continue
                    
                    # Buscar o crear cliente
                    cliente = Cliente.query.filter(
                        Cliente.nombre.contains(current_client)
                    ).first()
                    
                    if not cliente:
                        # Crear cliente si no existe
                        cliente = Cliente(
                            nombre=current_client,
                            ciudad='Málaga'  # Ciudad por defecto
                        )
                        db.session.add(cliente)
                        db.session.flush()
                    
                    clientes_procesados.add(cliente.nombre)
                    
                    # Parsear el nombre del menú
                    tipo_dieta, tipo_comida = parse_menu_name(menu_name_csv)
                    
                    # Procesar cada día de la semana
                    for col_idx in range(2, min(9, len(row))):  # Columnas C a I
                        if col_idx >= len(headers) or col_idx >= len(row):
                            continue
                        
                        dia_letra = headers[col_idx].strip()
                        if dia_letra not in DIAS_MAP:
                            continue
                        
                        cantidad_str = row[col_idx].strip()
                        if not cantidad_str or cantidad_str == '0':
                            continue
                        
                        try:
                            cantidad = int(cantidad_str)
                        except ValueError:
                            continue
                        
                        dia_enum = DIAS_MAP[dia_letra]
                        
                        # Crear albaranes para cada semana (1-4)
                        for num_semana in range(1, 5):
                            # Buscar el menú correspondiente
                            menu = find_menu(tipo_dieta, tipo_comida, num_semana, dia_enum)
                            
                            if not menu:
                                menu_key = f"{tipo_dieta} {tipo_comida} S{num_semana} {dia_enum.value}"
                                menus_no_encontrados.add(menu_key)
                                continue
                            
                            # Calcular fecha del albarán
                            week_start = get_week_start_date(num_semana, fecha_base)
                            dia_offset = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo'].index(dia_enum.value)
                            fecha_albaran = week_start + timedelta(days=dia_offset)
                            
                            # Buscar o crear albarán
                            albaran = Albaran.query.filter_by(
                                cliente_id=cliente.id,
                                fecha=fecha_albaran
                            ).first()
                            
                            if not albaran:
                                albaran = Albaran(
                                    referencia=Albaran.generar_referencia(),
                                    cliente_id=cliente.id,
                                    destinatario=cliente.nombre,
                                    fecha=fecha_albaran
                                )
                                db.session.add(albaran)
                                db.session.flush()
                                albaranes_creados += 1
                            
                            # Verificar si este menú ya está en el albarán
                            existing_detail = AlbaranDetalle.query.filter_by(
                                albaran_id=albaran.id,
                                menu_id=menu.id
                            ).first()
                            
                            if existing_detail:
                                # Actualizar cantidad
                                AlbaranDetalle.query.filter_by(
                                    albaran_id=albaran.id,
                                    menu_id=menu.id
                                ).delete()
                            
                            # Agregar platos del menú al albarán
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
                
                db.session.commit()
                
                # Mostrar resumen
                flash(f'Se crearon {albaranes_creados} albaranes nuevos', 'success')
                flash(f'Clientes procesados: {len(clientes_procesados)}', 'info')
                
                if menus_no_encontrados:
                    flash(f'Menús no encontrados: {len(menus_no_encontrados)} (ver detalles en consola)', 'warning')
                    print("\nMenús no encontrados:")
                    for menu in sorted(menus_no_encontrados):
                        print(f"  - {menu}")
                
                return redirect(url_for('albaranes.listar'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error al procesar el archivo: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Por favor, seleccione un archivo CSV', 'danger')
            return redirect(request.url)
    
    return render_template('albaranes_masivos/generar.html')