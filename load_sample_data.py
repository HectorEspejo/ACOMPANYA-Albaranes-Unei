#!/usr/bin/env python3
"""
Script to load sample data from model.csv into the database
"""

import csv
from datetime import datetime, timedelta
from app import create_app
from database import db
from database.models import (
    Ingrediente, Plato, Menu, TipoUnidad, TipoComida, 
    DiaSemana, platos_ingredientes, menus_platos
)
from sqlalchemy import insert

def load_sample_data():
    app = create_app()
    
    with app.app_context():
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing data...")
        db.drop_all()
        db.create_all()
        
        # Create some sample ingredients
        print("Creating sample ingredients...")
        ingredientes = [
            Ingrediente(
                nombre="LECHE",
                tipo_unidad=TipoUnidad.LITROS,
                stock_actual=100,
                fecha_caducidad=datetime.now().date() + timedelta(days=7),
                lote="L2025-001"
            ),
            Ingrediente(
                nombre="PAN",
                tipo_unidad=TipoUnidad.UNIDADES,
                stock_actual=200,
                fecha_caducidad=datetime.now().date() + timedelta(days=3),
                lote="P2025-001"
            ),
            Ingrediente(
                nombre="ACEITE OLIVA",
                tipo_unidad=TipoUnidad.LITROS,
                stock_actual=50,
                fecha_caducidad=datetime.now().date() + timedelta(days=180),
                lote="A2025-001"
            ),
            Ingrediente(
                nombre="TOMATE NATURAL TRITURADO",
                tipo_unidad=TipoUnidad.LITROS,
                stock_actual=30,
                fecha_caducidad=datetime.now().date() + timedelta(days=90),
                lote="T2025-001"
            ),
            Ingrediente(
                nombre="AZÚCAR",
                tipo_unidad=TipoUnidad.GRAMOS,
                stock_actual=5000,
                fecha_caducidad=datetime.now().date() + timedelta(days=365),
                lote="AZ2025-001"
            ),
            Ingrediente(
                nombre="CAFÉ SOLUBLE DESCAFEINADO",
                tipo_unidad=TipoUnidad.GRAMOS,
                stock_actual=2000,
                fecha_caducidad=datetime.now().date() + timedelta(days=365),
                lote="C2025-001"
            ),
            Ingrediente(
                nombre="LENTEJAS",
                tipo_unidad=TipoUnidad.GRAMOS,
                stock_actual=10000,
                fecha_caducidad=datetime.now().date() + timedelta(days=365),
                lote="LEN2025-001"
            ),
            Ingrediente(
                nombre="VERDURAS MIXTAS",
                tipo_unidad=TipoUnidad.GRAMOS,
                stock_actual=5000,
                fecha_caducidad=datetime.now().date() + timedelta(days=7),
                lote="V2025-001"
            ),
            Ingrediente(
                nombre="PATATAS",
                tipo_unidad=TipoUnidad.GRAMOS,
                stock_actual=15000,
                fecha_caducidad=datetime.now().date() + timedelta(days=30),
                lote="PAT2025-001"
            ),
            Ingrediente(
                nombre="CEBOLLA",
                tipo_unidad=TipoUnidad.GRAMOS,
                stock_actual=8000,
                fecha_caducidad=datetime.now().date() + timedelta(days=20),
                lote="CEB2025-001"
            ),
            Ingrediente(
                nombre="HUEVOS",
                tipo_unidad=TipoUnidad.UNIDADES,
                stock_actual=300,
                fecha_caducidad=datetime.now().date() + timedelta(days=14),
                lote="H2025-001"
            ),
            # Ingredientes que también son platos
            Ingrediente(
                nombre="PIEZA FRUTA",
                tipo_unidad=TipoUnidad.UNIDADES,
                stock_actual=500,
                fecha_caducidad=datetime.now().date() + timedelta(days=5),
                lote="F2025-001",
                es_plato=True
            ),
            Ingrediente(
                nombre="BIOFRUTAS",
                tipo_unidad=TipoUnidad.UNIDADES,
                stock_actual=200,
                fecha_caducidad=datetime.now().date() + timedelta(days=5),
                lote="BF2025-001",
                es_plato=True
            )
        ]
        
        for ing in ingredientes:
            db.session.add(ing)
        
        db.session.commit()
        print(f"Created {len(ingredientes)} ingredients")
        
        # Create sample dishes
        print("Creating sample dishes...")
        platos = [
            {
                "plato": Plato(
                    nombre="[298] LENTEJAS CON VERDURAS",
                    lote_propio="PL298-2025",
                    stock_actual=50,
                    unidad="raciones"
                ),
                "ingredientes": [
                    ("LENTEJAS", 200, "gramos"),
                    ("VERDURAS MIXTAS", 100, "gramos"),
                    ("ACEITE OLIVA", 0.02, "litros")
                ]
            },
            {
                "plato": Plato(
                    nombre="[22100] TORTILLA DE PATATAS CON CEBOLLA",
                    lote_propio="PL22100-2025",
                    stock_actual=30,
                    unidad="raciones"
                ),
                "ingredientes": [
                    ("PATATAS", 300, "gramos"),
                    ("CEBOLLA", 100, "gramos"),
                    ("HUEVOS", 3, "unidades"),
                    ("ACEITE OLIVA", 0.05, "litros")
                ]
            },
            {
                "plato": Plato(
                    nombre="[001] PAN",
                    lote_propio="PL001-2025",
                    stock_actual=100,
                    unidad="raciones"
                ),
                "ingredientes": [
                    ("PAN", 1, "unidades")
                ]
            },
            {
                "plato": Plato(
                    nombre="[10580] CAFE SOLUBLE DESCAFEINADO SOBRES 2GR",
                    lote_propio="PL10580-2025",
                    stock_actual=200,
                    unidad="sobres"
                ),
                "ingredientes": [
                    ("CAFÉ SOLUBLE DESCAFEINADO", 2, "gramos")
                ]
            },
            {
                "plato": Plato(
                    nombre="[20728] AZÚCAR SOBRES",
                    lote_propio="PL20728-2025",
                    stock_actual=300,
                    unidad="sobres"
                ),
                "ingredientes": [
                    ("AZÚCAR", 8, "gramos")
                ]
            },
            {
                "plato": Plato(
                    nombre="[20177] ACEITE OLIVA MONODOSIS",
                    lote_propio="PL20177-2025",
                    stock_actual=400,
                    unidad="monodosis"
                ),
                "ingredientes": [
                    ("ACEITE OLIVA", 0.01, "litros")
                ]
            },
            {
                "plato": Plato(
                    nombre="[18623] TOMATE NATURAL TRITURADO MONODOSIS",
                    lote_propio="PL18623-2025",
                    stock_actual=200,
                    unidad="monodosis"
                ),
                "ingredientes": [
                    ("TOMATE NATURAL TRITURADO", 0.02, "litros")
                ]
            }
        ]
        
        # Create dishes and their relationships
        for plato_data in platos:
            plato = plato_data["plato"]
            db.session.add(plato)
            db.session.flush()
            
            # Add ingredients to dish
            for ing_nombre, cantidad, unidad in plato_data["ingredientes"]:
                ingrediente = Ingrediente.query.filter_by(nombre=ing_nombre).first()
                if ingrediente:
                    stmt = insert(platos_ingredientes).values(
                        plato_id=plato.id,
                        ingrediente_id=ingrediente.id,
                        cantidad=cantidad,
                        unidad=unidad
                    )
                    db.session.execute(stmt)
        
        # Also add dishes from ingredients marked as es_plato
        for ing in Ingrediente.query.filter_by(es_plato=True).all():
            plato = Plato(
                nombre=ing.nombre,
                lote_propio=ing.lote,
                stock_actual=ing.stock_actual,
                unidad=ing.tipo_unidad.value
            )
            db.session.add(plato)
        
        db.session.commit()
        print(f"Created {Plato.query.count()} dishes")
        
        # Create sample menus
        print("Creating sample menus...")
        
        # Menu for Monday Week 1
        menu_lunes_almuerzo = Menu(
            nombre="MENÚ S1 LU AL (BASAL INDIVIDUAL)",
            dia_semana=DiaSemana.LUNES,
            numero_semana=1,
            tipo_dieta="basal",
            tipo_comida=TipoComida.ALMUERZO
        )
        db.session.add(menu_lunes_almuerzo)
        db.session.flush()
        
        # Add dishes to lunch menu
        platos_almuerzo = [
            ("[298] LENTEJAS CON VERDURAS", 1),
            ("[22100] TORTILLA DE PATATAS CON CEBOLLA", 1),
            ("[001] PAN", 1),
            ("PIEZA FRUTA", 1)
        ]
        
        for plato_nombre, cantidad in platos_almuerzo:
            plato = Plato.query.filter_by(nombre=plato_nombre).first()
            if plato:
                stmt = insert(menus_platos).values(
                    menu_id=menu_lunes_almuerzo.id,
                    plato_id=plato.id,
                    cantidad=cantidad
                )
                db.session.execute(stmt)
        
        # Menu for Monday breakfast
        menu_lunes_desayuno = Menu(
            nombre="DESAYUNO BASAL (Lunes)",
            dia_semana=DiaSemana.LUNES,
            numero_semana=1,
            tipo_dieta="basal",
            tipo_comida=TipoComida.DESAYUNO
        )
        db.session.add(menu_lunes_desayuno)
        db.session.flush()
        
        # Add dishes to breakfast menu
        platos_desayuno = [
            ("LECHE", 1),  # Assuming we have a dish for LECHE
            ("[10580] CAFE SOLUBLE DESCAFEINADO SOBRES 2GR", 1),
            ("[20728] AZÚCAR SOBRES", 1),
            ("[001] PAN", 1),
            ("[20177] ACEITE OLIVA MONODOSIS", 2),
            ("[18623] TOMATE NATURAL TRITURADO MONODOSIS", 1)
        ]
        
        # First create a LECHE dish if it doesn't exist
        leche_plato = Plato.query.filter_by(nombre="LECHE").first()
        if not leche_plato:
            leche_plato = Plato(
                nombre="LECHE",
                lote_propio="PLL-2025",
                stock_actual=100,
                unidad="raciones"
            )
            db.session.add(leche_plato)
            db.session.flush()
            
            # Link to ingredient
            leche_ing = Ingrediente.query.filter_by(nombre="LECHE").first()
            if leche_ing:
                stmt = insert(platos_ingredientes).values(
                    plato_id=leche_plato.id,
                    ingrediente_id=leche_ing.id,
                    cantidad=0.25,  # 250ml per serving
                    unidad="litros"
                )
                db.session.execute(stmt)
        
        for plato_nombre, cantidad in platos_desayuno:
            plato = Plato.query.filter_by(nombre=plato_nombre).first()
            if plato:
                stmt = insert(menus_platos).values(
                    menu_id=menu_lunes_desayuno.id,
                    plato_id=plato.id,
                    cantidad=cantidad
                )
                db.session.execute(stmt)
        
        # Menu for Monday snack
        menu_lunes_merienda = Menu(
            nombre="MERIENDA BASAL (Lunes)",
            dia_semana=DiaSemana.LUNES,
            numero_semana=1,
            tipo_dieta="basal",
            tipo_comida=TipoComida.MERIENDA
        )
        db.session.add(menu_lunes_merienda)
        db.session.flush()
        
        # Add dishes to snack menu
        platos_merienda = [
            ("BIOFRUTAS", 1),
            ("PIEZA FRUTA", 1)
        ]
        
        for plato_nombre, cantidad in platos_merienda:
            plato = Plato.query.filter_by(nombre=plato_nombre).first()
            if plato:
                stmt = insert(menus_platos).values(
                    menu_id=menu_lunes_merienda.id,
                    plato_id=plato.id,
                    cantidad=cantidad
                )
                db.session.execute(stmt)
        
        db.session.commit()
        print(f"Created {Menu.query.count()} menus")
        
        print("\nSample data loaded successfully!")
        print("\nYou can now:")
        print("1. Run the application with: python app.py")
        print("2. Access it at: http://localhost:5000")
        print("3. Create albaranes with the loaded menus and dishes")

if __name__ == "__main__":
    load_sample_data()