from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import db
from database.models import Plato, Ingrediente, platos_ingredientes
from sqlalchemy import insert

platos_bp = Blueprint('platos', __name__)

@platos_bp.route('/')
def listar():
    page = request.args.get('page', 1, type=int)
    platos = Plato.query.paginate(page=page, per_page=20, error_out=False)
    return render_template('platos/listar.html', platos=platos)

@platos_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo():
    if request.method == 'POST':
        try:
            plato = Plato(
                nombre=request.form['nombre'],
                lote_propio=request.form.get('lote_propio'),
                stock_actual=float(request.form.get('stock_actual', 0)),
                unidad=request.form.get('unidad', 'unidades')
            )
            
            db.session.add(plato)
            db.session.flush()  # Get the ID without committing
            
            # Add ingredients
            ingredientes_ids = request.form.getlist('ingrediente_id[]')
            cantidades = request.form.getlist('cantidad[]')
            unidades = request.form.getlist('unidad_ingrediente[]')
            
            for i, ing_id in enumerate(ingredientes_ids):
                if ing_id and cantidades[i]:
                    stmt = insert(platos_ingredientes).values(
                        plato_id=plato.id,
                        ingrediente_id=int(ing_id),
                        cantidad=float(cantidades[i]),
                        unidad=unidades[i]
                    )
                    db.session.execute(stmt)
            
            db.session.commit()
            flash('Plato creado exitosamente', 'success')
            return redirect(url_for('platos.listar'))
        except Exception as e:
            flash(f'Error al crear plato: {str(e)}', 'danger')
            db.session.rollback()
    
    ingredientes = Ingrediente.query.all()
    return render_template('platos/formulario.html', plato=None, ingredientes=ingredientes)

@platos_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    plato = Plato.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            plato.nombre = request.form['nombre']
            plato.lote_propio = request.form.get('lote_propio')
            plato.unidad = request.form.get('unidad', 'unidades')
            
            # Clear existing ingredients
            db.session.execute(platos_ingredientes.delete().where(platos_ingredientes.c.plato_id == plato.id))
            
            # Add new ingredients
            ingredientes_ids = request.form.getlist('ingrediente_id[]')
            cantidades = request.form.getlist('cantidad[]')
            unidades = request.form.getlist('unidad_ingrediente[]')
            
            for i, ing_id in enumerate(ingredientes_ids):
                if ing_id and cantidades[i]:
                    stmt = insert(platos_ingredientes).values(
                        plato_id=plato.id,
                        ingrediente_id=int(ing_id),
                        cantidad=float(cantidades[i]),
                        unidad=unidades[i]
                    )
                    db.session.execute(stmt)
            
            db.session.commit()
            flash('Plato actualizado exitosamente', 'success')
            return redirect(url_for('platos.listar'))
        except Exception as e:
            flash(f'Error al actualizar plato: {str(e)}', 'danger')
            db.session.rollback()
    
    ingredientes = Ingrediente.query.all()
    ingredientes_actuales = plato.obtener_ingredientes_con_cantidad()
    return render_template('platos/formulario.html', 
                         plato=plato, 
                         ingredientes=ingredientes,
                         ingredientes_actuales=ingredientes_actuales)

@platos_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    plato = Plato.query.get_or_404(id)
    try:
        db.session.delete(plato)
        db.session.commit()
        flash('Plato eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar plato: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('platos.listar'))

@platos_bp.route('/producir/<int:id>', methods=['GET', 'POST'])
def producir(id):
    plato = Plato.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            cantidad = float(request.form['cantidad'])
            plato.producir(cantidad)
            flash(f'Se produjeron {cantidad} unidades de {plato.nombre}', 'success')
            return redirect(url_for('platos.listar'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Error al producir plato: {str(e)}', 'danger')
            db.session.rollback()
    
    ingredientes = plato.obtener_ingredientes_con_cantidad()
    return render_template('platos/producir.html', plato=plato, ingredientes=ingredientes)

@platos_bp.route('/api/ingredientes')
def api_ingredientes():
    """API endpoint para obtener ingredientes (para select2 o similar)"""
    q = request.args.get('q', '')
    ingredientes = Ingrediente.query.filter(Ingrediente.nombre.contains(q)).all()
    return jsonify([{
        'id': ing.id,
        'text': ing.nombre,
        'tipo_unidad': ing.tipo_unidad.value,
        'stock_actual': ing.stock_actual
    } for ing in ingredientes])