from datetime import datetime, timedelta
from database.models import Ingrediente, Plato
from config import Config
from flask import current_app

def check_stock_alerts():
    """Check for low stock items"""
    alerts = []
    
    # Check ingredients
    low_stock_ingredients = Ingrediente.query.filter(
        Ingrediente.stock_actual < Config.STOCK_ALERT_THRESHOLD
    ).all()
    
    for ing in low_stock_ingredients:
        alerts.append({
            'type': 'low_stock',
            'entity': 'ingrediente',
            'item': ing,
            'message': f'Stock bajo de {ing.nombre}: {ing.stock_actual} {ing.tipo_unidad.value}'
        })
    
    # Check dishes
    low_stock_platos = Plato.query.filter(
        Plato.stock_actual < Config.STOCK_ALERT_THRESHOLD
    ).all()
    
    for plato in low_stock_platos:
        alerts.append({
            'type': 'low_stock',
            'entity': 'plato',
            'item': plato,
            'message': f'Stock bajo de {plato.nombre}: {plato.stock_actual} {plato.unidad}'
        })
    
    return alerts

def get_expiring_ingredients():
    """Get ingredients that are close to expiry"""
    alerts = []
    expiry_date = datetime.now().date() + timedelta(days=Config.EXPIRY_ALERT_DAYS)
    
    expiring = Ingrediente.query.filter(
        Ingrediente.fecha_caducidad <= expiry_date,
        Ingrediente.fecha_caducidad >= datetime.now().date()
    ).all()
    
    for ing in expiring:
        days_until = (ing.fecha_caducidad - datetime.now().date()).days
        alerts.append({
            'type': 'expiry',
            'entity': 'ingrediente',
            'item': ing,
            'days_until': days_until,
            'message': f'{ing.nombre} caduca en {days_until} días (Lote: {ing.lote})'
        })
    
    return alerts

def calculate_ingredient_requirements(plato, cantidad):
    """Calculate ingredient requirements for producing a quantity of a dish"""
    requirements = []
    debug_mode = current_app.config.get('DEBUG_MODE', False)
    
    for ingrediente, cantidad_necesaria, unidad in plato.obtener_ingredientes_con_cantidad():
        total_necesario = cantidad_necesaria * cantidad
        disponible = ingrediente.stock_actual
        suficiente = debug_mode or disponible >= total_necesario
        
        requirements.append({
            'ingrediente': ingrediente,
            'cantidad_necesaria': total_necesario,
            'unidad': unidad,
            'disponible': disponible,
            'suficiente': suficiente,
            'faltante': 0 if debug_mode else max(0, total_necesario - disponible) if not suficiente else 0
        })
    
    return requirements

def calculate_plato_requirements(menu, cantidad):
    """Calculate dish requirements for preparing a quantity of menus"""
    requirements = []
    debug_mode = current_app.config.get('DEBUG_MODE', False)
    
    for plato, cantidad_necesaria in menu.obtener_platos_con_cantidad():
        total_necesario = cantidad_necesaria * cantidad
        disponible = plato.stock_actual
        suficiente = debug_mode or disponible >= total_necesario
        
        requirements.append({
            'plato': plato,
            'cantidad_necesaria': total_necesario,
            'disponible': disponible,
            'suficiente': suficiente,
            'faltante': 0 if debug_mode else max(0, total_necesario - disponible) if not suficiente else 0
        })
    
    return requirements