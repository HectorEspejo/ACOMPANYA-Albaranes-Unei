#!/usr/bin/env python3
"""
Script para gestionar albaranes modelo - crear o eliminar
"""

from app import create_app
from database import db
from database.models import Cliente, Albaran, AlbaranDetalle
from datetime import datetime, date
import sys
import re

def get_dia_abreviado(dia_nombre):
    """Obtiene la abreviatura de dos letras del día"""
    dias_map = {
        'Lunes': 'LU',
        'Martes': 'MA',
        'Miércoles': 'MI',
        'Jueves': 'JU',
        'Viernes': 'VI',
        'Sábado': 'SA',
        'Domingo': 'DO'
    }
    return dias_map.get(dia_nombre, 'XX')

def es_albaran_modelo(referencia):
    """Verifica si una referencia corresponde a un albarán modelo"""
    # Patrón: XX-00-Resto donde XX es día y 00 es número
    pattern = r'^(LU|MA|MI|JU|VI|SA|DO)-\d{2}-.*'
    return bool(re.match(pattern, referencia))

def generar_referencia_modelo(dia_semana, num_semana, cliente_nombre):
    """
    Genera la referencia del albarán modelo
    Formato: XX-00-Cliente
    donde XX = día de la semana, 00 = número de semana
    """
    dia_abrev = get_dia_abreviado(dia_semana)
    return f"{dia_abrev}-{num_semana:02d}-{cliente_nombre}"

def crear_albaranes_modelo():
    """Crea albaranes modelo para todos los clientes"""
    app = create_app()
    
    with app.app_context():
        try:
            # Obtener todos los clientes
            clientes = Cliente.query.all()
            
            if not clientes:
                print("No hay clientes en la base de datos. Por favor, importe clientes primero.")
                return
            
            print(f"Encontrados {len(clientes)} clientes.")
            
            # Días de la semana
            dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
            
            # Contador de albaranes creados
            albaranes_creados = 0
            albaranes_existentes = 0
            
            # Para cada cliente
            for cliente in clientes:
                print(f"\nProcesando cliente: {cliente.nombre}")
                
                # Para cada semana (1-4)
                for num_semana in range(1, 5):
                    # Para cada día de la semana
                    for dia_semana in dias_semana:
                        # Generar referencia
                        referencia = generar_referencia_modelo(dia_semana, num_semana, cliente.nombre)
                        
                        # Verificar si ya existe
                        albaran_existente = Albaran.query.filter_by(referencia=referencia).first()
                        
                        if albaran_existente:
                            albaranes_existentes += 1
                        else:
                            # Crear nuevo albarán modelo
                            albaran = Albaran(
                                referencia=referencia,
                                fecha=date.today(),  # Fecha actual
                                cliente_id=cliente.id,
                                destinatario=f"{cliente.nombre} - {cliente.ciudad} - Semana {num_semana} - {dia_semana}"
                            )
                            db.session.add(albaran)
                            albaranes_creados += 1
                            
                            # Hacer commit cada 100 albaranes para evitar problemas de memoria
                            if albaranes_creados % 100 == 0:
                                db.session.commit()
                                print(f"  Creados {albaranes_creados} albaranes...")
            
            # Commit final
            db.session.commit()
            
            print(f"\n=== RESUMEN ===")
            print(f"Albaranes creados: {albaranes_creados}")
            print(f"Albaranes que ya existían: {albaranes_existentes}")
            print(f"Total esperado: {len(clientes) * 4 * 7} (28 por cliente)")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al crear albaranes: {str(e)}")
            sys.exit(1)

def eliminar_albaranes_modelo():
    """Elimina todos los albaranes modelo (sin detalles)"""
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar albaranes que parecen ser modelo
            todos_albaranes = Albaran.query.all()
            albaranes_modelo = []
            
            for albaran in todos_albaranes:
                # Verificar si es un albarán modelo y no tiene detalles
                if es_albaran_modelo(albaran.referencia) and albaran.detalles.count() == 0:
                    albaranes_modelo.append(albaran)
            
            if not albaranes_modelo:
                print("No se encontraron albaranes modelo vacíos para eliminar.")
                return
            
            print(f"Se encontraron {len(albaranes_modelo)} albaranes modelo vacíos.")
            print("Ejemplos:")
            for albaran in albaranes_modelo[:5]:
                print(f"  - {albaran.referencia}")
            
            if len(albaranes_modelo) > 5:
                print(f"  ... y {len(albaranes_modelo) - 5} más")
            
            confirmar = input(f"\n¿Está seguro de eliminar {len(albaranes_modelo)} albaranes modelo? (s/n): ")
            
            if confirmar.lower() == 's':
                for albaran in albaranes_modelo:
                    db.session.delete(albaran)
                
                db.session.commit()
                print(f"Se eliminaron {len(albaranes_modelo)} albaranes modelo.")
            else:
                print("Operación cancelada.")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error al eliminar albaranes: {str(e)}")
            sys.exit(1)

def listar_albaranes_modelo():
    """Lista estadísticas de albaranes modelo"""
    app = create_app()
    
    with app.app_context():
        clientes = Cliente.query.all()
        print("\n=== ESTADÍSTICAS DE ALBARANES MODELO ===")
        
        total_modelo = 0
        total_con_detalles = 0
        
        for cliente in clientes:
            albaranes = Albaran.query.filter_by(cliente_id=cliente.id).all()
            modelo_count = 0
            con_detalles_count = 0
            
            for albaran in albaranes:
                if es_albaran_modelo(albaran.referencia):
                    modelo_count += 1
                    if albaran.detalles.count() > 0:
                        con_detalles_count += 1
            
            if modelo_count > 0:
                print(f"\n{cliente.nombre}:")
                print(f"  - Albaranes modelo: {modelo_count}/28")
                print(f"  - Con productos: {con_detalles_count}")
                print(f"  - Vacíos: {modelo_count - con_detalles_count}")
            
            total_modelo += modelo_count
            total_con_detalles += con_detalles_count
        
        print(f"\n=== TOTALES ===")
        print(f"Total albaranes modelo: {total_modelo}")
        print(f"Con productos: {total_con_detalles}")
        print(f"Vacíos: {total_modelo - total_con_detalles}")

def menu_principal():
    """Menú principal del script"""
    print("\n=== GESTIÓN DE ALBARANES MODELO ===")
    print("1. Crear albaranes modelo para todos los clientes")
    print("2. Eliminar albaranes modelo vacíos")
    print("3. Ver estadísticas de albaranes modelo")
    print("4. Salir")
    
    opcion = input("\nSeleccione una opción (1-4): ")
    
    if opcion == '1':
        print("\nEsta opción creará 28 albaranes por cada cliente")
        print("(4 semanas x 7 días de la semana)")
        confirmar = input("\n¿Desea continuar? (s/n): ")
        if confirmar.lower() == 's':
            crear_albaranes_modelo()
    
    elif opcion == '2':
        eliminar_albaranes_modelo()
    
    elif opcion == '3':
        listar_albaranes_modelo()
    
    elif opcion == '4':
        print("Saliendo...")
        sys.exit(0)
    
    else:
        print("Opción no válida.")

if __name__ == '__main__':
    while True:
        menu_principal()
        input("\nPresione Enter para continuar...")