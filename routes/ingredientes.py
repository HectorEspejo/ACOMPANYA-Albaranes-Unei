from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from database.models import Ingrediente, TipoUnidad, TipoMovimiento
from datetime import datetime

ingredientes_bp = Blueprint('ingredientes', __name__)

@ingredientes_bp.route('/')
@login_required
def listar():
    page = request.args.get('page', 1, type=int)
    ingredientes = Ingrediente.query.paginate(page=page, per_page=20, error_out=False)
    return render_template('ingredientes/listar.html', ingredientes=ingredientes)

@ingredientes_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        try:
            ingrediente = Ingrediente(
                nombre=request.form['nombre'],
                tipo_unidad=TipoUnidad(request.form['tipo_unidad']),
                stock_actual=float(request.form.get('stock_actual', 0)),
                lote=request.form.get('lote'),
                es_plato=request.form.get('es_plato') == 'on'
            )
            
            fecha_caducidad = request.form.get('fecha_caducidad')
            if fecha_caducidad:
                ingrediente.fecha_caducidad = datetime.strptime(fecha_caducidad, '%Y-%m-%d').date()
            
            db.session.add(ingrediente)
            db.session.commit()
            
            flash('Ingrediente creado exitosamente', 'success')
            return redirect(url_for('ingredientes.listar'))
        except Exception as e:
            flash(f'Error al crear ingrediente: {str(e)}', 'danger')
            db.session.rollback()
    
    return render_template('ingredientes/formulario.html', ingrediente=None, tipos_unidad=TipoUnidad)

@ingredientes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    ingrediente = Ingrediente.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            ingrediente.nombre = request.form['nombre']
            ingrediente.tipo_unidad = TipoUnidad(request.form['tipo_unidad'])
            ingrediente.lote = request.form.get('lote')
            ingrediente.es_plato = request.form.get('es_plato') == 'on'
            
            fecha_caducidad = request.form.get('fecha_caducidad')
            if fecha_caducidad:
                ingrediente.fecha_caducidad = datetime.strptime(fecha_caducidad, '%Y-%m-%d').date()
            else:
                ingrediente.fecha_caducidad = None
            
            db.session.commit()
            flash('Ingrediente actualizado exitosamente', 'success')
            return redirect(url_for('ingredientes.listar'))
        except Exception as e:
            flash(f'Error al actualizar ingrediente: {str(e)}', 'danger')
            db.session.rollback()
    
    return render_template('ingredientes/formulario.html', ingrediente=ingrediente, tipos_unidad=TipoUnidad)

@ingredientes_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    ingrediente = Ingrediente.query.get_or_404(id)
    try:
        db.session.delete(ingrediente)
        db.session.commit()
        flash('Ingrediente eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar ingrediente: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('ingredientes.listar'))

@ingredientes_bp.route('/stock/<int:id>', methods=['GET', 'POST'])
@login_required
def ajustar_stock(id):
    ingrediente = Ingrediente.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            tipo_movimiento = TipoMovimiento(request.form['tipo_movimiento'])
            cantidad = float(request.form['cantidad'])
            motivo = request.form.get('motivo', '')
            
            ingrediente.actualizar_stock(cantidad, tipo_movimiento, motivo)
            flash('Stock actualizado exitosamente', 'success')
            return redirect(url_for('ingredientes.listar'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Error al actualizar stock: {str(e)}', 'danger')
            db.session.rollback()
    
    return render_template('ingredientes/ajustar_stock.html', 
                         ingrediente=ingrediente, 
                         tipos_movimiento=TipoMovimiento)