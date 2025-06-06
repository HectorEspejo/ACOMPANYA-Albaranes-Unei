from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database import db
from database.models import Cliente
import csv
import io

clientes_bp = Blueprint('clientes', __name__)

@clientes_bp.route('/')
def listar():
    """List all clients"""
    page = request.args.get('page', 1, type=int)
    busqueda = request.args.get('busqueda', '')
    ciudad = request.args.get('ciudad', '')
    
    query = Cliente.query
    
    if busqueda:
        query = query.filter(Cliente.nombre.contains(busqueda))
    if ciudad:
        query = query.filter(Cliente.ciudad.contains(ciudad))
    
    clientes = query.order_by(Cliente.nombre).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get unique cities for filter
    ciudades = db.session.query(Cliente.ciudad).distinct().order_by(Cliente.ciudad).all()
    ciudades = [c[0] for c in ciudades if c[0]]
    
    return render_template('clientes/listar.html', 
                         clientes=clientes,
                         ciudades=ciudades)

@clientes_bp.route('/nuevo', methods=['GET', 'POST'])
def nuevo():
    """Create new client"""
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        ciudad = request.form.get('ciudad', '').strip()
        
        if not nombre or not ciudad:
            flash('El nombre y la ciudad son obligatorios', 'danger')
            return redirect(request.url)
        
        # Check if client already exists
        cliente_existente = Cliente.query.filter_by(nombre=nombre).first()
        if cliente_existente:
            flash(f'Ya existe un cliente con el nombre "{nombre}"', 'warning')
            return redirect(request.url)
        
        try:
            cliente = Cliente(
                nombre=nombre,
                ciudad=ciudad
            )
            db.session.add(cliente)
            db.session.commit()
            flash('Cliente creado exitosamente', 'success')
            return redirect(url_for('clientes.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear cliente: {str(e)}', 'danger')
    
    return render_template('clientes/formulario.html', cliente=None)

@clientes_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    """Edit existing client"""
    cliente = Cliente.query.get_or_404(id)
    
    if request.method == 'POST':
        nombre = request.form.get('nombre', '').strip()
        ciudad = request.form.get('ciudad', '').strip()
        
        if not nombre or not ciudad:
            flash('El nombre y la ciudad son obligatorios', 'danger')
            return redirect(request.url)
        
        # Check if name is taken by another client
        otro_cliente = Cliente.query.filter(
            Cliente.nombre == nombre,
            Cliente.id != id
        ).first()
        
        if otro_cliente:
            flash(f'Ya existe otro cliente con el nombre "{nombre}"', 'warning')
            return redirect(request.url)
        
        try:
            cliente.nombre = nombre
            cliente.ciudad = ciudad
            db.session.commit()
            flash('Cliente actualizado exitosamente', 'success')
            return redirect(url_for('clientes.listar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar cliente: {str(e)}', 'danger')
    
    return render_template('clientes/formulario.html', cliente=cliente)

@clientes_bp.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    """Delete client"""
    cliente = Cliente.query.get_or_404(id)
    
    # Check if client has associated albarans
    if cliente.albaranes.count() > 0:
        flash(f'No se puede eliminar el cliente "{cliente.nombre}" porque tiene albaranes asociados', 'danger')
        return redirect(url_for('clientes.listar'))
    
    try:
        db.session.delete(cliente)
        db.session.commit()
        flash('Cliente eliminado exitosamente', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar cliente: {str(e)}', 'danger')
    
    return redirect(url_for('clientes.listar'))

@clientes_bp.route('/importar', methods=['GET', 'POST'])
def importar():
    """Import clients from CSV file"""
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
                
                clientes_creados = 0
                clientes_existentes = 0
                errores = []
                
                for row_num, row in enumerate(csv_reader, start=2):
                    # Try different possible column names
                    nombre = (row.get('Mostrar nombre') or 
                             row.get('Nombre') or 
                             row.get('nombre') or '').strip().strip('"')
                    
                    ciudad = (row.get('Ciudad') or 
                             row.get('ciudad') or '').strip().strip('"')
                    
                    if not nombre or not ciudad:
                        errores.append(f'Fila {row_num}: Faltan datos obligatorios')
                        continue
                    
                    # Check if client already exists
                    cliente_existente = Cliente.query.filter_by(nombre=nombre).first()
                    if cliente_existente:
                        clientes_existentes += 1
                    else:
                        # Create new client
                        cliente = Cliente(
                            nombre=nombre,
                            ciudad=ciudad
                        )
                        db.session.add(cliente)
                        clientes_creados += 1
                
                db.session.commit()
                
                # Show results
                if clientes_creados > 0:
                    flash(f'Se crearon {clientes_creados} clientes nuevos', 'success')
                if clientes_existentes > 0:
                    flash(f'{clientes_existentes} clientes ya existían y no se modificaron', 'info')
                if errores:
                    flash(f'Se encontraron {len(errores)} errores durante la importación', 'warning')
                
                return redirect(url_for('clientes.listar'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Error al importar: {str(e)}', 'danger')
                return redirect(request.url)
        else:
            flash('Por favor, seleccione un archivo CSV', 'danger')
            return redirect(request.url)
    
    return render_template('clientes/importar.html')

@clientes_bp.route('/exportar')
def exportar():
    """Export all clients to CSV"""
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    writer.writerow(['Mostrar nombre', 'Ciudad'])
    
    # Write client data
    for cliente in clientes:
        writer.writerow([cliente.nombre, cliente.ciudad])
    
    # Prepare response
    output.seek(0)
    from flask import Response
    
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=clientes_export.csv',
            'Content-Type': 'text/csv; charset=utf-8'
        }
    )
    
    # Add BOM for Excel compatibility
    response.data = '\ufeff' + response.data
    
    return response

@clientes_bp.route('/api/todos')
def api_todos():
    """API endpoint to get all clients"""
    clientes = Cliente.query.order_by(Cliente.nombre).all()
    return jsonify([{
        'id': c.id,
        'nombre': c.nombre,
        'ciudad': c.ciudad
    } for c in clientes])