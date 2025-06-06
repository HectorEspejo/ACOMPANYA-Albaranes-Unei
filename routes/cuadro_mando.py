from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required
from database import db
from database.models import Albaran, AlbaranDetalle, Menu, Plato, Cliente, TipoComida
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from collections import defaultdict
import csv
import io

cuadro_mando_bp = Blueprint('cuadro_mando', __name__)

@cuadro_mando_bp.route('/')
@login_required
def index():
    return render_template('cuadro_mando/index.html')

@cuadro_mando_bp.route('/api/estadisticas/platos')
@login_required
def estadisticas_platos():
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    # Validar fechas requeridas
    if not fecha_desde or not fecha_hasta:
        return jsonify({'error': 'Las fechas son requeridas'}), 400
    
    query = db.session.query(
        Plato.nombre,
        func.sum(AlbaranDetalle.cantidad_entregada).label('total_vendido')
    ).join(
        AlbaranDetalle, AlbaranDetalle.plato_id == Plato.id
    ).join(
        Albaran, Albaran.id == AlbaranDetalle.albaran_id
    ).filter(
        Albaran.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date(),
        Albaran.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    )
    
    resultados = query.group_by(Plato.id, Plato.nombre).order_by(func.sum(AlbaranDetalle.cantidad_entregada).desc()).all()
    
    return jsonify([{
        'plato': r.nombre,
        'cantidad': float(r.total_vendido)
    } for r in resultados])

@cuadro_mando_bp.route('/api/estadisticas/menus')
@login_required
def estadisticas_menus():
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    # Validar fechas requeridas
    if not fecha_desde or not fecha_hasta:
        return jsonify({'error': 'Las fechas son requeridas'}), 400
    
    query = db.session.query(
        Menu.nombre,
        Menu.tipo_comida,
        func.sum(AlbaranDetalle.cantidad_entregada).label('total_vendido')
    ).join(
        AlbaranDetalle, AlbaranDetalle.menu_id == Menu.id
    ).join(
        Albaran, Albaran.id == AlbaranDetalle.albaran_id
    ).filter(
        Albaran.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date(),
        Albaran.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    )
    
    resultados = query.group_by(Menu.id, Menu.nombre, Menu.tipo_comida).order_by(func.sum(AlbaranDetalle.cantidad_entregada).desc()).all()
    
    return jsonify([{
        'menu': r.nombre,
        'tipo_comida': r.tipo_comida.value if r.tipo_comida else None,
        'cantidad': float(r.total_vendido)
    } for r in resultados])

@cuadro_mando_bp.route('/api/estadisticas/menus-por-cliente')
@login_required
def estadisticas_menus_por_cliente():
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    # Validar fechas requeridas
    if not fecha_desde or not fecha_hasta:
        return jsonify({'error': 'Las fechas son requeridas'}), 400
    
    query = db.session.query(
        Cliente.nombre.label('cliente_nombre'),
        Menu.nombre.label('menu_nombre'),
        Menu.tipo_comida,
        func.sum(AlbaranDetalle.cantidad_entregada).label('total_vendido')
    ).join(
        Albaran, Albaran.cliente_id == Cliente.id
    ).join(
        AlbaranDetalle, Albaran.id == AlbaranDetalle.albaran_id
    ).join(
        Menu, AlbaranDetalle.menu_id == Menu.id
    ).filter(
        Albaran.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date(),
        Albaran.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    )
    
    resultados = query.group_by(
        Cliente.id, Cliente.nombre, 
        Menu.id, Menu.nombre, Menu.tipo_comida
    ).order_by(Cliente.nombre, Menu.nombre).all()
    
    return jsonify([{
        'cliente': r.cliente_nombre,
        'menu': r.menu_nombre,
        'tipo_comida': r.tipo_comida.value if r.tipo_comida else None,
        'cantidad': float(r.total_vendido)
    } for r in resultados])

# Endpoints de exportación CSV
@cuadro_mando_bp.route('/exportar/menus')
@login_required
def exportar_menus_csv():
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    if not fecha_desde or not fecha_hasta:
        return jsonify({'error': 'Las fechas son requeridas'}), 400
    
    # Obtener datos
    query = db.session.query(
        Menu.nombre,
        Menu.tipo_comida,
        func.sum(AlbaranDetalle.cantidad_entregada).label('total_vendido')
    ).join(
        AlbaranDetalle, AlbaranDetalle.menu_id == Menu.id
    ).join(
        Albaran, Albaran.id == AlbaranDetalle.albaran_id
    ).filter(
        Albaran.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date(),
        Albaran.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    )
    
    resultados = query.group_by(Menu.id, Menu.nombre, Menu.tipo_comida).order_by(func.sum(AlbaranDetalle.cantidad_entregada).desc()).all()
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(['Menú', 'Tipo de Comida', 'Unidades Vendidas'])
    
    # Data
    for r in resultados:
        writer.writerow([
            r.nombre,
            r.tipo_comida.value if r.tipo_comida else 'N/A',
            float(r.total_vendido)
        ])
    
    # Prepare response with BOM for Excel compatibility
    output.seek(0)
    csv_data = '\ufeff' + output.getvalue()
    
    response = Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=menus_{fecha_desde}_{fecha_hasta}.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )
    
    return response

@cuadro_mando_bp.route('/exportar/platos')
@login_required
def exportar_platos_csv():
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    if not fecha_desde or not fecha_hasta:
        return jsonify({'error': 'Las fechas son requeridas'}), 400
    
    # Obtener datos
    query = db.session.query(
        Plato.nombre,
        func.sum(AlbaranDetalle.cantidad_entregada).label('total_vendido')
    ).join(
        AlbaranDetalle, AlbaranDetalle.plato_id == Plato.id
    ).join(
        Albaran, Albaran.id == AlbaranDetalle.albaran_id
    ).filter(
        Albaran.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date(),
        Albaran.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    )
    
    resultados = query.group_by(Plato.id, Plato.nombre).order_by(func.sum(AlbaranDetalle.cantidad_entregada).desc()).all()
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(['Plato', 'Unidades Vendidas'])
    
    # Data
    for r in resultados:
        writer.writerow([
            r.nombre,
            float(r.total_vendido)
        ])
    
    # Prepare response with BOM for Excel compatibility
    output.seek(0)
    csv_data = '\ufeff' + output.getvalue()
    
    response = Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=platos_{fecha_desde}_{fecha_hasta}.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )
    
    return response

@cuadro_mando_bp.route('/exportar/clientes')
@login_required
def exportar_clientes_csv():
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    if not fecha_desde or not fecha_hasta:
        return jsonify({'error': 'Las fechas son requeridas'}), 400
    
    # Obtener datos
    query = db.session.query(
        Cliente.nombre.label('cliente_nombre'),
        Menu.nombre.label('menu_nombre'),
        Menu.tipo_comida,
        func.sum(AlbaranDetalle.cantidad_entregada).label('total_vendido')
    ).join(
        Albaran, Albaran.cliente_id == Cliente.id
    ).join(
        AlbaranDetalle, Albaran.id == AlbaranDetalle.albaran_id
    ).join(
        Menu, AlbaranDetalle.menu_id == Menu.id
    ).filter(
        Albaran.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date(),
        Albaran.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
    )
    
    resultados = query.group_by(
        Cliente.id, Cliente.nombre, 
        Menu.id, Menu.nombre, Menu.tipo_comida
    ).order_by(Cliente.nombre, Menu.nombre).all()
    
    # Crear CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Headers
    writer.writerow(['Cliente', 'Menú', 'Tipo de Comida', 'Unidades'])
    
    # Data
    for r in resultados:
        writer.writerow([
            r.cliente_nombre,
            r.menu_nombre,
            r.tipo_comida.value if r.tipo_comida else 'N/A',
            float(r.total_vendido)
        ])
    
    # Prepare response with BOM for Excel compatibility
    output.seek(0)
    csv_data = '\ufeff' + output.getvalue()
    
    response = Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=menus_por_cliente_{fecha_desde}_{fecha_hasta}.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )
    
    return response