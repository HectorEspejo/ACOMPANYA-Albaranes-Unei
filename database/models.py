from datetime import datetime
from database import db
from sqlalchemy import Enum
import enum
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class TipoUnidad(enum.Enum):
    UNIDADES = "unidades"
    GRAMOS = "gramos"
    LITROS = "litros"
    MILILITROS = "mililitros"

class TipoComida(enum.Enum):
    DESAYUNO = "desayuno"
    ALMUERZO = "almuerzo"
    CENA = "cena"
    MERIENDA = "merienda"

class DiaSemana(enum.Enum):
    LUNES = "lunes"
    MARTES = "martes"
    MIERCOLES = "miercoles"
    JUEVES = "jueves"
    VIERNES = "viernes"
    SABADO = "sabado"
    DOMINGO = "domingo"

class TipoMovimiento(enum.Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"
    AJUSTE = "ajuste"

class EntidadTipo(enum.Enum):
    INGREDIENTE = "ingrediente"
    PLATO = "plato"

# Association tables
platos_ingredientes = db.Table('platos_ingredientes',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('plato_id', db.Integer, db.ForeignKey('platos.id'), nullable=False),
    db.Column('ingrediente_id', db.Integer, db.ForeignKey('ingredientes.id'), nullable=False),
    db.Column('cantidad', db.Float, nullable=False),
    db.Column('unidad', db.String(50), nullable=False)
)

menus_platos = db.Table('menus_platos',
    db.Column('id', db.Integer, primary_key=True),
    db.Column('menu_id', db.Integer, db.ForeignKey('menus.id'), nullable=False),
    db.Column('plato_id', db.Integer, db.ForeignKey('platos.id'), nullable=False),
    db.Column('cantidad', db.Integer, nullable=False, default=1)
)

class Ingrediente(db.Model):
    __tablename__ = 'ingredientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    tipo_unidad = db.Column(Enum(TipoUnidad), nullable=False)
    stock_actual = db.Column(db.Float, nullable=False, default=0)
    fecha_caducidad = db.Column(db.Date, nullable=True)
    lote = db.Column(db.String(100), nullable=True)
    es_plato = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    movimientos = db.relationship('MovimientoStock', 
                                 primaryjoin="and_(MovimientoStock.entidad_tipo=='ingrediente', "
                                           "MovimientoStock.entidad_id==Ingrediente.id)",
                                 foreign_keys='MovimientoStock.entidad_id',
                                 backref='ingrediente_ref',
                                 lazy='dynamic',
                                 overlaps="plato_ref,movimientos")
    
    def __repr__(self):
        return f'<Ingrediente {self.nombre}>'
    
    def actualizar_stock(self, cantidad, tipo_movimiento, motivo="", referencia=""):
        """Actualiza el stock y registra el movimiento"""
        if tipo_movimiento == TipoMovimiento.SALIDA:
            if not current_app.config.get('DEBUG_MODE', False) and self.stock_actual < cantidad:
                raise ValueError(f"Stock insuficiente. Stock actual: {self.stock_actual}, solicitado: {cantidad}")
            self.stock_actual -= cantidad
        elif tipo_movimiento == TipoMovimiento.ENTRADA:
            self.stock_actual += cantidad
        else:  # AJUSTE
            self.stock_actual = cantidad
        
        # Registrar movimiento
        movimiento = MovimientoStock(
            tipo_movimiento=tipo_movimiento,
            entidad_tipo=EntidadTipo.INGREDIENTE,
            entidad_id=self.id,
            cantidad=cantidad,
            motivo=motivo,
            referencia_documento=referencia
        )
        db.session.add(movimiento)
        db.session.commit()

class Plato(db.Model):
    __tablename__ = 'platos'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    lote_propio = db.Column(db.String(100), nullable=True)
    stock_actual = db.Column(db.Float, nullable=False, default=0)
    unidad = db.Column(db.String(50), nullable=False, default='unidades')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    ingredientes = db.relationship('Ingrediente', secondary=platos_ingredientes, backref='platos')
    movimientos = db.relationship('MovimientoStock', 
                                 primaryjoin="and_(MovimientoStock.entidad_tipo=='plato', "
                                           "MovimientoStock.entidad_id==Plato.id)",
                                 foreign_keys='MovimientoStock.entidad_id',
                                 backref='plato_ref',
                                 lazy='dynamic',
                                 overlaps="ingrediente_ref,movimientos")
    detalles_albaran = db.relationship('AlbaranDetalle', backref='plato', lazy='dynamic')
    
    def __repr__(self):
        return f'<Plato {self.nombre}>'
    
    def obtener_ingredientes_con_cantidad(self):
        """Obtiene los ingredientes con sus cantidades"""
        result = db.session.query(
            Ingrediente, 
            platos_ingredientes.c.cantidad,
            platos_ingredientes.c.unidad
        ).join(
            platos_ingredientes, 
            platos_ingredientes.c.ingrediente_id == Ingrediente.id
        ).filter(
            platos_ingredientes.c.plato_id == self.id
        ).all()
        return result
    
    def producir(self, cantidad_platos):
        """Produce una cantidad de platos, actualizando stocks"""
        # Verificar disponibilidad de ingredientes (saltar en modo debug)
        if not current_app.config.get('DEBUG_MODE', False):
            for ingrediente, cantidad_necesaria, _ in self.obtener_ingredientes_con_cantidad():
                total_necesario = cantidad_necesaria * cantidad_platos
                if ingrediente.stock_actual < total_necesario:
                    raise ValueError(f"Stock insuficiente de {ingrediente.nombre}. "
                                   f"Necesario: {total_necesario}, Disponible: {ingrediente.stock_actual}")
        
        # Descontar ingredientes
        for ingrediente, cantidad_necesaria, _ in self.obtener_ingredientes_con_cantidad():
            total_necesario = cantidad_necesaria * cantidad_platos
            ingrediente.actualizar_stock(total_necesario, TipoMovimiento.SALIDA, 
                                       f"Producción de {cantidad_platos} {self.nombre}")
        
        # Aumentar stock del plato
        self.stock_actual += cantidad_platos
        movimiento = MovimientoStock(
            tipo_movimiento=TipoMovimiento.ENTRADA,
            entidad_tipo=EntidadTipo.PLATO,
            entidad_id=self.id,
            cantidad=cantidad_platos,
            motivo=f"Producción de {cantidad_platos} unidades"
        )
        db.session.add(movimiento)
        db.session.commit()
    
    def obtener_lotes_trazabilidad(self):
        """Obtiene todos los lotes de los ingredientes para trazabilidad"""
        lotes = [self.lote_propio] if self.lote_propio else []
        for ingrediente in self.ingredientes:
            if ingrediente.lote:
                lotes.append(f"{ingrediente.nombre}: {ingrediente.lote}")
        return lotes

class Menu(db.Model):
    __tablename__ = 'menus'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False)
    dia_semana = db.Column(Enum(DiaSemana), nullable=False)
    numero_semana = db.Column(db.Integer, nullable=False)
    tipo_dieta = db.Column(db.String(100), nullable=False, default='basal')
    tipo_comida = db.Column(Enum(TipoComida), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    platos = db.relationship('Plato', secondary=menus_platos, backref='menus')
    detalles_albaran = db.relationship('AlbaranDetalle', backref='menu', lazy='dynamic')
    
    def __repr__(self):
        return f'<Menu {self.nombre} - S{self.numero_semana} {self.dia_semana.value}>'
    
    def obtener_platos_con_cantidad(self):
        """Obtiene los platos con sus cantidades"""
        result = db.session.query(
            Plato, 
            menus_platos.c.cantidad
        ).join(
            menus_platos, 
            menus_platos.c.plato_id == Plato.id
        ).filter(
            menus_platos.c.menu_id == self.id
        ).all()
        return result
    
    def preparar_menu(self, cantidad_menus):
        """Prepara una cantidad de menús, actualizando stocks de platos"""
        # Verificar disponibilidad de platos (saltar en modo debug)
        if not current_app.config.get('DEBUG_MODE', False):
            for plato, cantidad_necesaria in self.obtener_platos_con_cantidad():
                total_necesario = cantidad_necesaria * cantidad_menus
                if plato.stock_actual < total_necesario:
                    raise ValueError(f"Stock insuficiente de {plato.nombre}. "
                                   f"Necesario: {total_necesario}, Disponible: {plato.stock_actual}")
        
        # Descontar platos
        for plato, cantidad_necesaria in self.obtener_platos_con_cantidad():
            total_necesario = cantidad_necesaria * cantidad_menus
            plato.stock_actual -= total_necesario
            movimiento = MovimientoStock(
                tipo_movimiento=TipoMovimiento.SALIDA,
                entidad_tipo=EntidadTipo.PLATO,
                entidad_id=plato.id,
                cantidad=total_necesario,
                motivo=f"Preparación de {cantidad_menus} menús {self.nombre}"
            )
            db.session.add(movimiento)
        
        db.session.commit()
    
    def obtener_lotes_completos(self):
        """Obtiene todos los lotes de todos los platos del menú"""
        lotes_por_plato = {}
        for plato in self.platos:
            lotes_por_plato[plato.nombre] = plato.obtener_lotes_trazabilidad()
        return lotes_por_plato

class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, unique=True)
    ciudad = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    albaranes = db.relationship('Albaran', backref='cliente', lazy='dynamic')
    
    def __repr__(self):
        return f'<Cliente {self.nombre}>'

class Albaran(db.Model):
    __tablename__ = 'albaranes'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    referencia = db.Column(db.String(100), unique=True, nullable=False)
    destinatario = db.Column(db.String(200), nullable=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    detalles = db.relationship('AlbaranDetalle', backref='albaran', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Albaran {self.referencia} - {self.fecha}>'
    
    @staticmethod
    def generar_referencia():
        """Genera una referencia única para el albarán"""
        fecha_str = datetime.now().strftime('%Y%m%d')
        # Contar solo referencias que empiecen con fecha (formato: YYYYMMDD-####)
        count = Albaran.query.filter(Albaran.referencia.like(f'{fecha_str}-%')).count()
        return f'{fecha_str}-{count + 1:04d}'

class AlbaranDetalle(db.Model):
    __tablename__ = 'albaranes_detalles'
    
    id = db.Column(db.Integer, primary_key=True)
    albaran_id = db.Column(db.Integer, db.ForeignKey('albaranes.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'), nullable=True)
    plato_id = db.Column(db.Integer, db.ForeignKey('platos.id'), nullable=False)
    cantidad_entregada = db.Column(db.Float, nullable=False)
    unidad = db.Column(db.String(50), nullable=False)
    lote = db.Column(db.String(500), nullable=True)  # Puede contener múltiples lotes separados por comas
    
    def __repr__(self):
        return f'<AlbaranDetalle {self.plato.nombre} x{self.cantidad_entregada}>'

class MovimientoStock(db.Model):
    __tablename__ = 'movimientos_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_movimiento = db.Column(Enum(TipoMovimiento), nullable=False)
    entidad_tipo = db.Column(Enum(EntidadTipo), nullable=False)
    entidad_id = db.Column(db.Integer, nullable=False)
    cantidad = db.Column(db.Float, nullable=False)
    motivo = db.Column(db.String(500), nullable=True)
    referencia_documento = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MovimientoStock {self.tipo_movimiento.value} {self.cantidad}>'

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre_usuario = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Usuario {self.nombre_usuario}>'