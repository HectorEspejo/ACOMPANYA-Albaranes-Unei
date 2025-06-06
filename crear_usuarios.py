#!/usr/bin/env python3
"""
Script para crear usuarios en el sistema de albaranes.
Uso: python crear_usuarios.py
"""

from database import init_db
from database.models import Usuario
from flask import Flask
from config import Config
import getpass

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    init_db(app)
    return app

def crear_usuario(nombre_usuario, password):
    """Crear un nuevo usuario en la base de datos"""
    try:
        # Verificar si el usuario ya existe
        usuario_existente = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
        if usuario_existente:
            print(f"❌ El usuario '{nombre_usuario}' ya existe.")
            return False
        
        # Crear nuevo usuario
        nuevo_usuario = Usuario(nombre_usuario=nombre_usuario)
        nuevo_usuario.set_password(password)
        
        from database import db
        db.session.add(nuevo_usuario)
        db.session.commit()
        
        print(f"✅ Usuario '{nombre_usuario}' creado exitosamente.")
        return True
        
    except Exception as e:
        print(f"❌ Error al crear usuario: {e}")
        return False

def listar_usuarios():
    """Listar todos los usuarios existentes"""
    usuarios = Usuario.query.all()
    if not usuarios:
        print("No hay usuarios registrados.")
        return
    
    print("\n📋 Usuarios registrados:")
    print("-" * 40)
    for usuario in usuarios:
        print(f"• {usuario.nombre_usuario} (ID: {usuario.id})")

def eliminar_usuario(nombre_usuario):
    """Eliminar un usuario de la base de datos"""
    try:
        usuario = Usuario.query.filter_by(nombre_usuario=nombre_usuario).first()
        if not usuario:
            print(f"❌ El usuario '{nombre_usuario}' no existe.")
            return False
        
        from database import db
        db.session.delete(usuario)
        db.session.commit()
        
        print(f"✅ Usuario '{nombre_usuario}' eliminado exitosamente.")
        return True
        
    except Exception as e:
        print(f"❌ Error al eliminar usuario: {e}")
        return False

def menu_principal():
    """Mostrar menú principal"""
    while True:
        print("\n" + "="*50)
        print("🔐 GESTIÓN DE USUARIOS - Sistema de Albaranes")
        print("="*50)
        print("1. Crear nuevo usuario")
        print("2. Listar usuarios existentes")
        print("3. Eliminar usuario")
        print("4. Salir")
        print("-" * 50)
        
        opcion = input("Seleccione una opción (1-4): ").strip()
        
        if opcion == "1":
            print("\n📝 Crear nuevo usuario")
            nombre_usuario = input("Nombre de usuario: ").strip()
            if not nombre_usuario:
                print("❌ El nombre de usuario no puede estar vacío.")
                continue
                
            password = getpass.getpass("Contraseña: ")
            if not password:
                print("❌ La contraseña no puede estar vacía.")
                continue
                
            password_confirm = getpass.getpass("Confirmar contraseña: ")
            if password != password_confirm:
                print("❌ Las contraseñas no coinciden.")
                continue
            
            crear_usuario(nombre_usuario, password)
            
        elif opcion == "2":
            listar_usuarios()
            
        elif opcion == "3":
            print("\n🗑️ Eliminar usuario")
            listar_usuarios()
            nombre_usuario = input("\nNombre de usuario a eliminar: ").strip()
            if nombre_usuario:
                confirmar = input(f"¿Está seguro de eliminar el usuario '{nombre_usuario}'? (s/N): ").strip().lower()
                if confirmar == 's':
                    eliminar_usuario(nombre_usuario)
                else:
                    print("Operación cancelada.")
            
        elif opcion == "4":
            print("👋 ¡Hasta luego!")
            break
            
        else:
            print("❌ Opción no válida. Seleccione 1-4.")

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        print("🚀 Inicializando base de datos...")
        from database import db
        db.create_all()
        print("✅ Base de datos inicializada.")
        
        menu_principal()