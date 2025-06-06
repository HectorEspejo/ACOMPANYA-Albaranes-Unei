from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from database import db
from database.models import Menu, Plato, DiaSemana, TipoComida, menus_platos
from sqlalchemy import insert

menus_bp = Blueprint('menus', __name__)

@menus_bp.route('/')
@login_required
def listar():
    page = request.args.get('page', 1, type=int)
    semana = request.args.get('semana', type=int)
    tipo_dieta = request.args.get('tipo_dieta')
    
    query = Menu.query
    if semana:
        query = query.filter(Menu.numero_semana == semana)
    if tipo_dieta:
        query = query.filter(Menu.tipo_dieta == tipo_dieta)
    
    menus = query.order_by(Menu.numero_semana.desc(), Menu.dia_semana).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('menus/listar.html', menus=menus)

@menus_bp.route('/nuevo', methods=['GET', 'POST'])
@login_required
def nuevo():
    if request.method == 'POST':
        try:
            menu = Menu(
                nombre=request.form['nombre'],
                dia_semana=DiaSemana(request.form['dia_semana']),
                numero_semana=int(request.form['numero_semana']),
                tipo_dieta=request.form.get('tipo_dieta', 'basal'),
                tipo_comida=TipoComida(request.form['tipo_comida'])
            )
            
            db.session.add(menu)
            db.session.flush()
            
            # Add platos
            platos_ids = request.form.getlist('plato_id[]')
            cantidades = request.form.getlist('cantidad_plato[]')
            
            for i, plato_id in enumerate(platos_ids):
                if plato_id and cantidades[i]:
                    stmt = insert(menus_platos).values(
                        menu_id=menu.id,
                        plato_id=int(plato_id),
                        cantidad=int(cantidades[i])
                    )
                    db.session.execute(stmt)
            
            db.session.commit()
            flash('Menú creado exitosamente', 'success')
            return redirect(url_for('menus.listar'))
        except Exception as e:
            flash(f'Error al crear menú: {str(e)}', 'danger')
            db.session.rollback()
    
    platos = Plato.query.all()
    return render_template('menus/formulario.html', 
                         menu=None, 
                         platos=platos,
                         dias_semana=DiaSemana,
                         tipos_comida=TipoComida)

@menus_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    menu = Menu.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            menu.nombre = request.form['nombre']
            menu.dia_semana = DiaSemana(request.form['dia_semana'])
            menu.numero_semana = int(request.form['numero_semana'])
            menu.tipo_dieta = request.form.get('tipo_dieta', 'basal')
            menu.tipo_comida = TipoComida(request.form['tipo_comida'])
            
            # Clear existing platos
            db.session.execute(menus_platos.delete().where(menus_platos.c.menu_id == menu.id))
            
            # Add new platos
            platos_ids = request.form.getlist('plato_id[]')
            cantidades = request.form.getlist('cantidad_plato[]')
            
            for i, plato_id in enumerate(platos_ids):
                if plato_id and cantidades[i]:
                    stmt = insert(menus_platos).values(
                        menu_id=menu.id,
                        plato_id=int(plato_id),
                        cantidad=int(cantidades[i])
                    )
                    db.session.execute(stmt)
            
            db.session.commit()
            flash('Menú actualizado exitosamente', 'success')
            return redirect(url_for('menus.listar'))
        except Exception as e:
            flash(f'Error al actualizar menú: {str(e)}', 'danger')
            db.session.rollback()
    
    platos = Plato.query.all()
    platos_actuales = menu.obtener_platos_con_cantidad()
    return render_template('menus/formulario.html', 
                         menu=menu, 
                         platos=platos,
                         platos_actuales=platos_actuales,
                         dias_semana=DiaSemana,
                         tipos_comida=TipoComida)

@menus_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    menu = Menu.query.get_or_404(id)
    try:
        db.session.delete(menu)
        db.session.commit()
        flash('Menú eliminado exitosamente', 'success')
    except Exception as e:
        flash(f'Error al eliminar menú: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('menus.listar'))

@menus_bp.route('/preparar/<int:id>', methods=['GET', 'POST'])
@login_required
def preparar(id):
    menu = Menu.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            cantidad = int(request.form['cantidad'])
            menu.preparar_menu(cantidad)
            flash(f'Se prepararon {cantidad} menús {menu.nombre}', 'success')
            return redirect(url_for('menus.listar'))
        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f'Error al preparar menú: {str(e)}', 'danger')
            db.session.rollback()
    
    platos = menu.obtener_platos_con_cantidad()
    return render_template('menus/preparar.html', menu=menu, platos=platos)

@menus_bp.route('/calendario')
@login_required
def calendario():
    """Vista de calendario semanal de menús"""
    semana = request.args.get('semana', 1, type=int)
    tipo_dieta = request.args.get('tipo_dieta', 'basal')
    
    menus = Menu.query.filter(
        Menu.numero_semana == semana,
        Menu.tipo_dieta == tipo_dieta
    ).all()
    
    # Organizar por día y tipo de comida
    calendario = {}
    for dia in DiaSemana:
        calendario[dia] = {}
        for tipo in TipoComida:
            calendario[dia][tipo] = None
    
    for menu in menus:
        calendario[menu.dia_semana][menu.tipo_comida] = menu
    
    return render_template('menus/calendario.html', 
                         calendario=calendario,
                         semana=semana,
                         tipo_dieta=tipo_dieta,
                         dias_semana=DiaSemana,
                         tipos_comida=TipoComida)