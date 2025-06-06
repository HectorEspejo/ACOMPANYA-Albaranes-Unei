from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response, Response, jsonify
from database import db
from database.models import Albaran, AlbaranDetalle, Menu, Plato, Cliente, DiaSemana
from datetime import datetime
from collections import defaultdict
import csv
import io

albaranes_bp = Blueprint('albaranes', __name__)

@albaranes_bp.route('/')
def listar():
    page = request.args.get('page', 1, type=int)
    fecha_desde = request.args.get('fecha_desde')
    fecha_hasta = request.args.get('fecha_hasta')
    
    query = Albaran.query
    
    if fecha_desde:
        query = query.filter(Albaran.fecha >= datetime.strptime(fecha_desde, '%Y-%m-%d').date())
    if fecha_hasta:
        query = query.filter(Albaran.fecha <= datetime.strptime(fecha_hasta, '%Y-%m-%d').date())
    
    albaranes = query.order_by(Albaran.fecha.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('albaranes/listar.html', albaranes=albaranes)

@albaranes_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo():
    if request.method == 'POST':
        try:
            # Create albaran
            cliente_id = request.form.get('cliente_id')
            if cliente_id:
                cliente_id = int(cliente_id) if cliente_id != '' else None
            else:
                cliente_id = None
                
            albaran = Albaran(
                referencia=Albaran.generar_referencia(),
                destinatario=request.form.get('destinatario', ''),
                cliente_id=cliente_id,
                fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            )
            
            db.session.add(albaran)
            db.session.flush()
            
            # Process menus
            menu_ids = request.form.getlist('menu_id[]')
            cantidades_menu = request.form.getlist('cantidad_menu[]')
            
            for i, menu_id in enumerate(menu_ids):
                if menu_id and cantidades_menu[i]:
                    menu = Menu.query.get(int(menu_id))
                    cantidad = int(cantidades_menu[i])
                    
                    # For each menu, add its dishes to the albaran
                    for plato, cantidad_plato in menu.obtener_platos_con_cantidad():
                        # Get lot information
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
                    
                    # Update stock
                    menu.preparar_menu(cantidad)
            
            # Process individual dishes (not part of menus)
            plato_ids = request.form.getlist('plato_individual_id[]')
            cantidades_plato = request.form.getlist('cantidad_plato_individual[]')
            
            for i, plato_id in enumerate(plato_ids):
                if plato_id and cantidades_plato[i]:
                    plato = Plato.query.get(int(plato_id))
                    cantidad = float(cantidades_plato[i])
                    
                    # Get lot information
                    lotes = ', '.join(plato.obtener_lotes_trazabilidad())
                    
                    detalle = AlbaranDetalle(
                        albaran_id=albaran.id,
                        menu_id=None,
                        plato_id=plato.id,
                        cantidad_entregada=cantidad,
                        unidad=plato.unidad,
                        lote=lotes
                    )
                    db.session.add(detalle)
                    
                    # Update stock
                    plato.stock_actual -= cantidad
            
            db.session.commit()
            flash('Albarán creado exitosamente', 'success')
            return redirect(url_for('albaranes.ver', id=albaran.id))
            
        except Exception as e:
            flash(f'Error al crear albarán: {str(e)}', 'danger')
            db.session.rollback()
    
    menus = Menu.query.order_by(Menu.numero_semana.desc(), Menu.dia_semana).all()
    platos = Plato.query.filter(Plato.stock_actual > 0).all()
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    
    return render_template('albaranes/formulario.html', 
                         albaran=None, 
                         menus=menus, 
                         platos=platos,
                         clientes=clientes)

@albaranes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    albaran = Albaran.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Update basic albaran info
            albaran.fecha = datetime.strptime(request.form['fecha'], '%Y-%m-%d').date()
            albaran.destinatario = request.form.get('destinatario', '')
            
            cliente_id = request.form.get('cliente_id')
            if cliente_id:
                albaran.cliente_id = int(cliente_id) if cliente_id != '' else None
            else:
                albaran.cliente_id = None
            
            # First, restore stock from existing details
            for detalle in albaran.detalles:
                if detalle.menu_id:
                    # If it's from a menu, we need to restore the dish stock
                    detalle.plato.stock_actual += detalle.cantidad_entregada
                else:
                    # Individual dish
                    detalle.plato.stock_actual += detalle.cantidad_entregada
            
            # Delete existing details
            AlbaranDetalle.query.filter_by(albaran_id=albaran.id).delete()
            
            # Process menus (same as create)
            menu_ids = request.form.getlist('menu_id[]')
            cantidades_menu = request.form.getlist('cantidad_menu[]')
            
            for i, menu_id in enumerate(menu_ids):
                if menu_id and cantidades_menu[i]:
                    menu = Menu.query.get(int(menu_id))
                    cantidad = int(cantidades_menu[i])
                    
                    # For each menu, add its dishes to the albaran
                    for plato, cantidad_plato in menu.obtener_platos_con_cantidad():
                        # Get lot information
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
                    
                    # Update stock
                    menu.preparar_menu(cantidad)
            
            # Process individual dishes
            plato_ids = request.form.getlist('plato_individual_id[]')
            cantidades_plato = request.form.getlist('cantidad_plato_individual[]')
            
            for i, plato_id in enumerate(plato_ids):
                if plato_id and cantidades_plato[i]:
                    plato = Plato.query.get(int(plato_id))
                    cantidad = float(cantidades_plato[i])
                    
                    # Get lot information
                    lotes = ', '.join(plato.obtener_lotes_trazabilidad())
                    
                    detalle = AlbaranDetalle(
                        albaran_id=albaran.id,
                        menu_id=None,
                        plato_id=plato.id,
                        cantidad_entregada=cantidad,
                        unidad=plato.unidad,
                        lote=lotes
                    )
                    db.session.add(detalle)
                    
                    # Update stock
                    plato.stock_actual -= cantidad
            
            db.session.commit()
            flash('Albarán actualizado exitosamente', 'success')
            return redirect(url_for('albaranes.ver', id=albaran.id))
            
        except Exception as e:
            flash(f'Error al actualizar albarán: {str(e)}', 'danger')
            db.session.rollback()
    
    # Prepare data for the form
    menus = Menu.query.order_by(Menu.numero_semana.desc(), Menu.dia_semana).all()
    platos = Plato.query.all()  # Show all dishes, not just with stock
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    
    # Organize existing details
    detalles_por_menu = defaultdict(list)
    detalles_individuales = []
    menus_en_albaran = {}
    
    for detalle in albaran.detalles:
        if detalle.menu_id:
            detalles_por_menu[detalle.menu].append(detalle)
            if detalle.menu_id not in menus_en_albaran:
                # Calculate menu quantity based on dish quantities
                menu = detalle.menu
                platos_menu = menu.obtener_platos_con_cantidad()
                if platos_menu:
                    primera_cantidad = platos_menu[0][1]  # Quantity of first dish in menu
                    if primera_cantidad > 0:
                        menus_en_albaran[detalle.menu_id] = {
                            'menu': menu,
                            'cantidad': int(detalle.cantidad_entregada / primera_cantidad)
                        }
        else:
            detalles_individuales.append(detalle)
    
    return render_template('albaranes/editar.html', 
                         albaran=albaran,
                         menus=menus,
                         platos=platos,
                         clientes=clientes,
                         menus_en_albaran=menus_en_albaran,
                         detalles_individuales=detalles_individuales)

@albaranes_bp.route('/ver/<int:id>')
def ver(id):
    albaran = Albaran.query.get_or_404(id)
    
    # Organize details by menu
    detalles_por_menu = defaultdict(list)
    detalles_individuales = []
    
    for detalle in albaran.detalles:
        if detalle.menu_id:
            detalles_por_menu[detalle.menu].append(detalle)
        else:
            detalles_individuales.append(detalle)
    
    return render_template('albaranes/ver.html', 
                         albaran=albaran,
                         detalles_por_menu=dict(detalles_por_menu),
                         detalles_individuales=detalles_individuales)

@albaranes_bp.route('/imprimir/<int:id>')
def imprimir(id):
    albaran = Albaran.query.get_or_404(id)
    
    # Organize details by menu
    detalles_por_menu = defaultdict(list)
    detalles_individuales = []
    
    for detalle in albaran.detalles:
        if detalle.menu_id:
            detalles_por_menu[detalle.menu].append(detalle)
        else:
            detalles_individuales.append(detalle)
    
    html = render_template('albaranes/imprimir.html', 
                         albaran=albaran,
                         detalles_por_menu=dict(detalles_por_menu),
                         detalles_individuales=detalles_individuales)
    
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html'
    return response

@albaranes_bp.route('/exportar/<int:id>')
def exportar_csv(id):
    albaran = Albaran.query.get_or_404(id)
    
    # Organize details by menu
    detalles_por_menu = defaultdict(list)
    detalles_individuales = []
    
    for detalle in albaran.detalles:
        if detalle.menu_id:
            detalles_por_menu[detalle.menu].append(detalle)
        else:
            detalles_individuales.append(detalle)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write table headers (matching the format)
    writer.writerow(['PRODUCTO', 'UNIDADES', 'REFERENCIA'])
    
    # Write menu details
    for menu, detalles in detalles_por_menu.items():
        # Format: nombre + dia_semana + tipo_comida + tipo_dieta
        menu_name = f'** {menu.nombre} {menu.dia_semana.value.upper()} {menu.tipo_comida.value.upper()} {menu.tipo_dieta}'
        writer.writerow([menu_name, '', ''])
        for detalle in detalles:
            # Extract only the plate's lot (not ingredient lots)
            plato_lote = detalle.plato.lote_propio or ''
            writer.writerow([
                detalle.plato.nombre,
                str(int(detalle.cantidad_entregada)) if detalle.cantidad_entregada.is_integer() else str(detalle.cantidad_entregada),
                plato_lote
            ])
    
    # Write individual dishes
    if detalles_individuales:
        writer.writerow(['** PLATOS INDIVIDUALES', '', ''])
        for detalle in detalles_individuales:
            # Extract only the plate's lot (not ingredient lots)
            plato_lote = detalle.plato.lote_propio or ''
            writer.writerow([
                detalle.plato.nombre,
                str(int(detalle.cantidad_entregada)) if detalle.cantidad_entregada.is_integer() else str(detalle.cantidad_entregada),
                plato_lote
            ])
    
    # Prepare response
    output.seek(0)
    # Add BOM for Excel compatibility with Spanish characters
    csv_content = '\ufeff' + output.getvalue()
    
    response = Response(
        csv_content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=albaran_{albaran.referencia}.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )
    
    return response

@albaranes_bp.route('/exportar-multiple', methods=['POST'])
def exportar_multiple_csv():
    """Export multiple albarans to a single CSV file"""
    albaran_ids = request.form.getlist('albaran_ids[]')
    
    if not albaran_ids:
        flash('No se seleccionaron albaranes para exportar', 'warning')
        return redirect(url_for('albaranes.listar'))
    
    # Get all selected albarans
    albaranes = Albaran.query.filter(Albaran.id.in_(albaran_ids)).order_by(Albaran.fecha).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Process each albaran
    for i, albaran in enumerate(albaranes):
        # Add blank line between albarans except for the first one
        if i > 0:
            writer.writerow([])
        
        # Write header
        writer.writerow(['Referencia', 'Fecha', 'Cliente', 'Ciudad', 'Destinatario'])
        
        # Write albaran info
        cliente_info = albaran.cliente.nombre if albaran.cliente else ''
        ciudad_info = albaran.cliente.ciudad if albaran.cliente else ''
        destinatario_info = albaran.destinatario if albaran.destinatario else ''
        
        # Create a combined destinatario field that includes client info
        if albaran.cliente and destinatario_info:
            destinatario_completo = f"{cliente_info}, {destinatario_info} - {ciudad_info}"
        elif destinatario_info:
            destinatario_completo = destinatario_info
        else:
            destinatario_completo = ''
        
        writer.writerow([
            albaran.referencia,
            albaran.fecha.strftime('%d/%m/%Y'),
            cliente_info,
            destinatario_info,
            ciudad_info,
            destinatario_completo
        ])
        
        # Write units header
        writer.writerow(['Unidades', 'Menú'])
        
        # Group details by menu and count quantities
        menu_counts = defaultdict(float)
        
        for detalle in albaran.detalles:
            if detalle.menu_id:
                menu = detalle.menu
                # Format: tipo_dieta + S + numero_semana + dia_semana + tipo_comida + dia_semana_upper + tipo_comida_upper + tipo_dieta
                menu_key = f"{menu.tipo_dieta.upper()} S{menu.numero_semana} {menu.dia_semana.value.capitalize()} {menu.tipo_comida.value.capitalize()} {menu.dia_semana.value.upper()} {menu.tipo_comida.value.upper()} {menu.tipo_dieta.upper()}"
                menu_counts[menu_key] += detalle.cantidad_entregada
        
        # Write menu quantities
        for menu_name, cantidad in menu_counts.items():
            cantidad_str = str(int(cantidad)) if cantidad.is_integer() else str(cantidad)
            writer.writerow([f"{cantidad_str} Uds. ** {menu_name}", '', ''])
    
    # Prepare response
    output.seek(0)
    # Add BOM for Excel compatibility with Spanish characters
    csv_content = '\ufeff' + output.getvalue()
    
    response = Response(
        csv_content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename=albaranes_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )
    
    return response

@albaranes_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    albaran = Albaran.query.get_or_404(id)
    try:
        # Log para depuración
        print(f"Eliminando albarán ID: {id}, Referencia: {albaran.referencia}")
        
        # Restore stock before deleting
        for detalle in albaran.detalles:
            if detalle.menu_id:
                # If it's from a menu, restore the dish stock
                detalle.plato.stock_actual += detalle.cantidad_entregada
            else:
                # Individual dish
                detalle.plato.stock_actual += detalle.cantidad_entregada
        
        db.session.delete(albaran)
        db.session.commit()
        print(f"Albarán {id} eliminado correctamente de la base de datos")
        flash('Albarán eliminado exitosamente y stock restaurado', 'success')
    except Exception as e:
        print(f"Error al eliminar albarán {id}: {str(e)}")
        flash(f'Error al eliminar albarán: {str(e)}', 'danger')
        db.session.rollback()
    
    return redirect(url_for('albaranes.listar'))

@albaranes_bp.route('/api/menus/<int:menu_id>/platos')
def api_menu_platos(menu_id):
    """Get dishes for a specific menu (for dynamic form updates)"""
    menu = Menu.query.get_or_404(menu_id)
    platos_data = []
    
    for plato, cantidad in menu.obtener_platos_con_cantidad():
        platos_data.append({
            'id': plato.id,
            'nombre': plato.nombre,
            'cantidad': cantidad,
            'unidad': plato.unidad,
            'stock': plato.stock_actual,
            'lotes': plato.obtener_lotes_trazabilidad()
        })
    
    return {'platos': platos_data}

@albaranes_bp.route('/duplicar/<int:id>', methods=['GET', 'POST'])
def duplicar(id):
    albaran_original = Albaran.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Get target week and day
            semana_destino = int(request.form.get('semana_destino'))
            dia_destino = request.form.get('dia_destino')
            fecha_destino = datetime.strptime(request.form.get('fecha_destino'), '%Y-%m-%d').date()
            
            # Create new albaran
            nuevo_albaran = Albaran(
                referencia=Albaran.generar_referencia(),
                destinatario=albaran_original.destinatario,
                cliente_id=albaran_original.cliente_id,
                fecha=fecha_destino
            )
            
            db.session.add(nuevo_albaran)
            db.session.flush()
            
            # Track warnings for menus not found
            warnings = []
            
            # Group details by menu to avoid duplicating menu processing
            menus_procesados = {}
            detalles_individuales = []
            
            for detalle_original in albaran_original.detalles:
                if detalle_original.menu_id:
                    if detalle_original.menu_id not in menus_procesados:
                        menus_procesados[detalle_original.menu_id] = detalle_original
                else:
                    detalles_individuales.append(detalle_original)
            
            # Process menus (only once per menu)
            for menu_id, detalle_original in menus_procesados.items():
                menu_original = detalle_original.menu
                
                # Find corresponding menu for the target week and day
                menu_destino = Menu.query.filter_by(
                    tipo_dieta=menu_original.tipo_dieta,
                    tipo_comida=menu_original.tipo_comida,
                    numero_semana=semana_destino,
                    dia_semana=DiaSemana(dia_destino)
                ).first()
                
                if menu_destino:
                    # Calculate quantity of menus from original
                    platos_menu_original = menu_original.obtener_platos_con_cantidad()
                    if platos_menu_original:
                        primera_cantidad = platos_menu_original[0][1]
                        if primera_cantidad > 0:
                            cantidad_menus = int(detalle_original.cantidad_entregada / primera_cantidad)
                            
                            # Add dishes from destination menu
                            for plato, cantidad_plato in menu_destino.obtener_platos_con_cantidad():
                                lotes = ', '.join(plato.obtener_lotes_trazabilidad())
                                
                                nuevo_detalle = AlbaranDetalle(
                                    albaran_id=nuevo_albaran.id,
                                    menu_id=menu_destino.id,
                                    plato_id=plato.id,
                                    cantidad_entregada=cantidad_plato * cantidad_menus,
                                    unidad=plato.unidad,
                                    lote=lotes
                                )
                                db.session.add(nuevo_detalle)
                            
                            # Update stock
                            menu_destino.preparar_menu(cantidad_menus)
                else:
                    # Menu not found for target day/week
                    warnings.append(f"No se encontró el menú '{menu_original.nombre}' para la semana {semana_destino} y día {dia_destino}")
            
            # Process individual dishes
            for detalle_original in detalles_individuales:
                plato = detalle_original.plato
                lotes = ', '.join(plato.obtener_lotes_trazabilidad())
                
                nuevo_detalle = AlbaranDetalle(
                    albaran_id=nuevo_albaran.id,
                    menu_id=None,
                    plato_id=plato.id,
                    cantidad_entregada=detalle_original.cantidad_entregada,
                    unidad=plato.unidad,
                    lote=lotes
                )
                db.session.add(nuevo_detalle)
                
                # Update stock
                plato.stock_actual -= detalle_original.cantidad_entregada
            
            db.session.commit()
            
            # Show warnings if any
            for warning in warnings:
                flash(warning, 'warning')
            
            if not warnings:
                flash('Albarán duplicado exitosamente', 'success')
            else:
                flash('Albarán duplicado con advertencias', 'info')
                
            return redirect(url_for('albaranes.ver', id=nuevo_albaran.id))
            
        except Exception as e:
            flash(f'Error al duplicar albarán: {str(e)}', 'danger')
            db.session.rollback()
            return redirect(url_for('albaranes.duplicar', id=id))
    
    # GET request - show duplication form
    # Analyze original albaran to extract week and day info
    semana_original = None
    dia_original = None
    
    for detalle in albaran_original.detalles:
        if detalle.menu_id:
            semana_original = detalle.menu.numero_semana
            dia_original = detalle.menu.dia_semana.value
            break
    
    return render_template('albaranes/duplicar.html',
                         albaran=albaran_original,
                         semana_original=semana_original,
                         dia_original=dia_original)

@albaranes_bp.route('/api/verificar-menus', methods=['POST'])
def api_verificar_menus():
    """Verify if menus exist for target week and day"""
    data = request.get_json()
    albaran_id = data.get('albaran_id')
    semana_destino = data.get('semana_destino')
    dia_destino = data.get('dia_destino')
    
    albaran = Albaran.query.get_or_404(albaran_id)
    menus_faltantes = []
    menus_encontrados = []
    
    # Check each menu in the original albaran
    menus_procesados = set()
    for detalle in albaran.detalles:
        if detalle.menu_id and detalle.menu_id not in menus_procesados:
            menus_procesados.add(detalle.menu_id)
            menu_original = detalle.menu
            
            # Look for corresponding menu
            menu_destino = Menu.query.filter_by(
                tipo_dieta=menu_original.tipo_dieta,
                tipo_comida=menu_original.tipo_comida,
                numero_semana=semana_destino,
                dia_semana=DiaSemana(dia_destino)
            ).first()
            
            if menu_destino:
                menus_encontrados.append({
                    'original': menu_original.nombre,
                    'destino': menu_destino.nombre
                })
            else:
                menus_faltantes.append({
                    'nombre': menu_original.nombre,
                    'tipo_dieta': menu_original.tipo_dieta,
                    'tipo_comida': menu_original.tipo_comida.value
                })
    
    return jsonify({
        'menus_faltantes': menus_faltantes,
        'menus_encontrados': menus_encontrados,
        'puede_duplicar': len(menus_faltantes) == 0
    })