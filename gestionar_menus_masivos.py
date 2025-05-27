#!/usr/bin/env python3
"""
Script para gestionar menús creados masivamente
Permite eliminar menús vacíos o listar estadísticas
"""

from app import create_app
from database import db
from database.models import Menu
from datetime import datetime
import sys

def listar_estadisticas_menus():
    """Lista estadísticas de menús por tipo"""
    app = create_app()
    
    with app.app_context():
        # Agrupar por tipo_dieta
        tipos_dieta = db.session.query(Menu.tipo_dieta).distinct().order_by(Menu.tipo_dieta).all()
        
        print("\n=== ESTADÍSTICAS DE MENÚS POR TIPO ===")
        
        total_menus = 0
        total_con_platos = 0
        
        for (tipo,) in tipos_dieta:
            menus_tipo = Menu.query.filter_by(tipo_dieta=tipo).all()
            con_platos = sum(1 for m in menus_tipo if m.platos)
            
            print(f"\n{tipo}:")
            print(f"  Total menús: {len(menus_tipo)}")
            print(f"  Con platos: {con_platos}")
            print(f"  Vacíos: {len(menus_tipo) - con_platos}")
            
            total_menus += len(menus_tipo)
            total_con_platos += con_platos
        
        print(f"\n=== TOTALES ===")
        print(f"Total menús: {total_menus}")
        print(f"Con platos: {total_con_platos}")
        print(f"Vacíos: {total_menus - total_con_platos}")

def eliminar_menus_vacios(tipo_dieta=None):
    """Elimina menús que no tienen platos asociados"""
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar menús vacíos
            query = Menu.query
            if tipo_dieta:
                query = query.filter_by(tipo_dieta=tipo_dieta)
            
            todos_menus = query.all()
            menus_vacios = [m for m in todos_menus if not m.platos]
            
            if not menus_vacios:
                print("No se encontraron menús vacíos.")
                return
            
            print(f"Se encontraron {len(menus_vacios)} menús vacíos.")
            print("Ejemplos:")
            for menu in menus_vacios[:5]:
                print(f"  - {menu.nombre}")
            
            if len(menus_vacios) > 5:
                print(f"  ... y {len(menus_vacios) - 5} más")
            
            confirmar = input(f"\n¿Está seguro de eliminar {len(menus_vacios)} menús vacíos? (s/n): ")
            
            if confirmar.lower() == 's':
                for menu in menus_vacios:
                    db.session.delete(menu)
                
                db.session.commit()
                print(f"Se eliminaron {len(menus_vacios)} menús vacíos.")
            else:
                print("Operación cancelada.")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar menús: {str(e)}")
            sys.exit(1)

def listar_tipos_dieta():
    """Lista todos los tipos de dieta disponibles"""
    app = create_app()
    
    with app.app_context():
        tipos = db.session.query(Menu.tipo_dieta).distinct().order_by(Menu.tipo_dieta).all()
        print("\n=== TIPOS DE DIETA DISPONIBLES ===")
        for i, (tipo,) in enumerate(tipos, 1):
            print(f"{i}. {tipo}")
        return [tipo[0] for tipo in tipos]

def menu_principal():
    """Menú principal del script"""
    print("\n=== GESTIÓN DE MENÚS MASIVOS ===")
    print("1. Ver estadísticas de menús")
    print("2. Eliminar todos los menús vacíos")
    print("3. Eliminar menús vacíos de un tipo específico")
    print("4. Salir")
    
    opcion = input("\nSeleccione una opción (1-4): ")
    
    if opcion == '1':
        listar_estadisticas_menus()
    
    elif opcion == '2':
        eliminar_menus_vacios()
    
    elif opcion == '3':
        tipos = listar_tipos_dieta()
        if tipos:
            try:
                num = int(input("\nSeleccione el número del tipo de dieta: "))
                if 1 <= num <= len(tipos):
                    tipo_seleccionado = tipos[num - 1]
                    print(f"\nEliminando menús vacíos del tipo: {tipo_seleccionado}")
                    eliminar_menus_vacios(tipo_seleccionado)
                else:
                    print("Número no válido.")
            except ValueError:
                print("Entrada no válida.")
    
    elif opcion == '4':
        print("Saliendo...")
        sys.exit(0)
    
    else:
        print("Opción no válida.")

if __name__ == '__main__':
    while True:
        menu_principal()
        input("\nPresione Enter para continuar...")