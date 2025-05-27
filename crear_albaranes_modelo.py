#!/usr/bin/env python3
"""
Script para crear albaranes modelo para cada cliente
Crea un albarán por cada semana (1-4) y día de la semana (Lunes-Domingo)
Total: 28 albaranes por cliente (4 semanas x 7 días)
"""

from app import create_app
from database import db
from database.models import Cliente, Albaran
from datetime import datetime, date
import sys

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

def generar_referencia_modelo(dia_semana, num_semana, cliente_nombre):
    """
    Genera la referencia del albarán modelo
    Formato: XX-00-Cliente
    donde XX = día de la semana, 00 = número de semana
    """
    dia_abrev = get_dia_abreviado(dia_semana)
    return f"{dia_abrev}-{num_semana:02d}-{cliente_nombre}"

def crear_albaranes_modelo():
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

def verificar_albaranes():
    """Función auxiliar para verificar los albaranes creados"""
    app = create_app()
    
    with app.app_context():
        clientes = Cliente.query.all()
        print("\n=== VERIFICACIÓN ===")
        for cliente in clientes[:3]:  # Mostrar solo los primeros 3 clientes
            count = Albaran.query.filter_by(cliente_id=cliente.id).count()
            print(f"{cliente.nombre}: {count} albaranes")
            
            # Mostrar algunos ejemplos
            ejemplos = Albaran.query.filter_by(cliente_id=cliente.id).limit(3).all()
            for ej in ejemplos:
                print(f"  - {ej.referencia}")

if __name__ == '__main__':
    print("=== CREACIÓN DE ALBARANES MODELO ===")
    print("Este script creará 28 albaranes por cada cliente")
    print("(4 semanas x 7 días de la semana)")
    
    respuesta = input("\n¿Desea continuar? (s/n): ")
    
    if respuesta.lower() == 's':
        print("\nCreando albaranes modelo...")
        crear_albaranes_modelo()
        
        # Opcionalmente verificar
        respuesta_verificar = input("\n¿Desea ver una verificación de los albaranes creados? (s/n): ")
        if respuesta_verificar.lower() == 's':
            verificar_albaranes()
    else:
        print("Operación cancelada.")