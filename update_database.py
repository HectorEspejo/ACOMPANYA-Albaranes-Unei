#!/usr/bin/env python3
"""
Script para actualizar la base de datos con las nuevas tablas y columnas
"""

from app import create_app
from database import db
from sqlalchemy import text
import sys

def update_database():
    app = create_app()
    
    with app.app_context():
        try:
            # Verificar si la tabla clientes existe
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'clientes' not in tables:
                print("Creando tabla 'clientes'...")
                # Crear tabla clientes
                with db.engine.connect() as conn:
                    conn.execute(text('''
                        CREATE TABLE clientes (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            nombre VARCHAR(200) NOT NULL UNIQUE,
                            ciudad VARCHAR(100) NOT NULL,
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        )
                    '''))
                    conn.commit()
                print("Tabla 'clientes' creada exitosamente.")
            else:
                print("La tabla 'clientes' ya existe.")
            
            # Verificar si la columna cliente_id existe en albaranes
            columns = [col['name'] for col in inspector.get_columns('albaranes')]
            
            if 'cliente_id' not in columns:
                print("Añadiendo columna 'cliente_id' a la tabla 'albaranes'...")
                with db.engine.connect() as conn:
                    conn.execute(text('''
                        ALTER TABLE albaranes ADD COLUMN cliente_id INTEGER REFERENCES clientes(id)
                    '''))
                    conn.commit()
                print("Columna 'cliente_id' añadida exitosamente.")
            else:
                print("La columna 'cliente_id' ya existe en la tabla 'albaranes'.")
            
            print("\nBase de datos actualizada correctamente.")
            
        except Exception as e:
            print(f"Error al actualizar la base de datos: {str(e)}")
            sys.exit(1)

if __name__ == '__main__':
    print("Actualizando la base de datos...")
    update_database()