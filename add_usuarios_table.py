#!/usr/bin/env python3
"""
Script para añadir la tabla de usuarios a la base de datos existente.
Este script es seguro de ejecutar múltiples veces - no duplicará la tabla si ya existe.
"""

import sqlite3
import sys
from datetime import datetime

def create_usuarios_table():
    """Crear la tabla de usuarios en la base de datos"""
    try:
        # Conectar a la base de datos
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        print("🔌 Conectado a la base de datos...")
        
        # Verificar si la tabla ya existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='usuarios'
        """)
        
        if cursor.fetchone():
            print("⚠️  La tabla 'usuarios' ya existe en la base de datos.")
            response = input("¿Desea ver los usuarios existentes? (s/N): ").strip().lower()
            
            if response == 's':
                cursor.execute("SELECT id, nombre_usuario, created_at FROM usuarios")
                usuarios = cursor.fetchall()
                
                if usuarios:
                    print("\n📋 Usuarios existentes:")
                    print("-" * 60)
                    for usuario in usuarios:
                        fecha = datetime.fromisoformat(usuario[2]).strftime("%d/%m/%Y %H:%M")
                        print(f"ID: {usuario[0]} | Usuario: {usuario[1]} | Creado: {fecha}")
                else:
                    print("\n❌ No hay usuarios registrados.")
            
            conn.close()
            return False
        
        # Crear la tabla de usuarios
        print("🔨 Creando tabla 'usuarios'...")
        
        cursor.execute("""
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_usuario VARCHAR(80) NOT NULL UNIQUE,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Crear índice en nombre_usuario para búsquedas más rápidas
        cursor.execute("""
            CREATE INDEX idx_usuarios_nombre_usuario 
            ON usuarios(nombre_usuario)
        """)
        
        # Confirmar los cambios
        conn.commit()
        
        print("✅ Tabla 'usuarios' creada exitosamente.")
        print("✅ Índice en 'nombre_usuario' creado exitosamente.")
        
        # Mostrar información sobre la tabla creada
        cursor.execute("PRAGMA table_info(usuarios)")
        columns = cursor.fetchall()
        
        print("\n📊 Estructura de la tabla 'usuarios':")
        print("-" * 60)
        for col in columns:
            print(f"Campo: {col[1]:<20} Tipo: {col[2]:<20} Nulo: {'Sí' if col[3] == 0 else 'No':<5} PK: {'Sí' if col[5] == 1 else 'No'}")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error de base de datos: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def verify_database_integrity():
    """Verificar la integridad de la base de datos"""
    try:
        conn = sqlite3.connect('database/database.db')
        cursor = conn.cursor()
        
        # Verificar que podamos leer las tablas
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table'
            ORDER BY name
        """)
        
        tables = cursor.fetchall()
        print("\n📋 Tablas en la base de datos:")
        print("-" * 40)
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"• {table[0]:<30} ({count} registros)")
        
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error verificando la base de datos: {e}")
        return False

def main():
    """Función principal"""
    print("=" * 60)
    print("🗄️  AÑADIR TABLA DE USUARIOS A LA BASE DE DATOS")
    print("=" * 60)
    
    # Verificar que existe el archivo de base de datos
    try:
        with open('database/database.db', 'rb'):
            pass
    except FileNotFoundError:
        print("❌ No se encuentra el archivo 'database/database.db'")
        print("   Asegúrese de ejecutar este script desde el directorio raíz del proyecto.")
        return 1
    
    # Crear la tabla
    success = create_usuarios_table()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ PROCESO COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        
        # Verificar integridad
        print("\n🔍 Verificando integridad de la base de datos...")
        verify_database_integrity()
        
        print("\n💡 Siguiente paso:")
        print("   Ejecute 'python crear_usuarios.py' para crear usuarios del sistema.")
        
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())