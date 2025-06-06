# 🍽️ ALBA - Sistema de Gestión de Albaranes

Sistema integral de gestión para cocinas y caterings que permite administrar ingredientes, platos, menús y generar albaranes de entrega con control de stock y trazabilidad completa.

## 📋 Funcionalidades Principales

### 🥄 Gestión de Ingredientes
- **Control de Stock**: Inventario en tiempo real con diferentes unidades de medida
- **Trazabilidad**: Seguimiento de lotes y fechas de caducidad
- **Movimientos**: Registro automático de entradas, salidas y ajustes
- **Importación**: Carga masiva desde archivos CSV

### 🍗 Gestión de Platos
- **Recetas**: Definición de ingredientes necesarios para cada plato
- **Producción**: Preparación de lotes con descuento automático de stock
- **Stock**: Control de platos preparados disponibles
- **Trazabilidad**: Seguimiento de ingredientes utilizados por lote

### 🍽️ Gestión de Menús
- **Composición**: Combinación de múltiples platos por tipo de comida
- **Calendario**: Planificación de menús por día de la semana
- **Preparación**: Producción masiva con control de disponibilidad
- **Tipos**: Categorización por desayuno, almuerzo, cena, merienda

### 👥 Gestión de Clientes
- **Base de Datos**: Registro de clientes con información de contacto
- **Importación**: Carga masiva desde archivos CSV
- **Historial**: Seguimiento de pedidos por cliente

### 📄 Sistema de Albaranes
- **Generación Individual**: Creación de albaranes personalizados
- **Generación Masiva**: Albaranes automáticos para múltiples clientes
- **Duplicación**: Copia de albaranes existentes con ajustes
- **Impresión**: Formato optimizado para impresión
- **Exportación**: Descarga en formato CSV

### 📊 Cuadro de Mando
- **Análisis de Ventas**: Estadísticas detalladas por período
- **Visualización**: Gráficos interactivos y tablas dinámicas
- **Métricas**: 
  - Unidades de menús vendidos por tipo
  - Platos más populares
  - Ventas por cliente
- **Exportación**: Reportes en CSV
- **Filtros**: Análisis por rangos de fechas personalizables

### 🔐 Sistema de Autenticación
- **Login Obligatorio**: Acceso protegido a todas las funcionalidades
- **Gestión de Usuarios**: Base de datos segura con contraseñas hasheadas
- **Sesiones Seguras**: Control de sesiones con Flask-Login
- **Script de Gestión**: Herramienta administrativa para crear/eliminar usuarios
- **Interfaz Intuitiva**: Login responsive con validación de credenciales

### 📥 Sistema de Importación
- **Tipos de Menú**: Definición de categorías de comida
- **Menús Masivos**: Carga de múltiples menús con platos
- **Inventario**: Importación de stock inicial
- **Platos**: Carga masiva con recetas incluidas

## 🔧 Tecnologías Utilizadas

### Backend
- **Flask**: Framework web de Python
- **Flask-Login**: Sistema de autenticación y sesiones
- **SQLAlchemy**: ORM para base de datos
- **SQLite**: Base de datos embebida
- **Python 3.10+**: Lenguaje de programación
- **Werkzeug**: Utilidades WSGI y hashing seguro

### Frontend
- **Bootstrap 4**: Framework CSS responsivo
- **jQuery**: Biblioteca JavaScript
- **DataTables**: Tablas interactivas con búsqueda y ordenamiento
- **Chart.js**: Gráficos interactivos
- **Font Awesome**: Iconografía

### Características Técnicas
- **Arquitectura MVC**: Separación clara de responsabilidades
- **Blueprints**: Modularización de rutas
- **Sistema de Login**: Autenticación obligatoria con Flask-Login
- **Validación**: Control de datos y relaciones
- **Manejo de Errores**: Sistema robusto de excepciones
- **Modo Debug**: Funcionalidad especial para desarrollo

## 📁 Estructura del Proyecto

```
alabaranes-unei2/
├── app.py                 # Aplicación principal
├── config.py             # Configuración
├── database/             # Modelos de base de datos
│   ├── __init__.py
│   ├── models.py
│   └── database.db
├── routes/               # Rutas por módulo
│   ├── albaranes.py
│   ├── albaranes_masivos.py
│   ├── clientes.py
│   ├── cuadro_mando.py
│   ├── importar.py
│   ├── ingredientes.py
│   ├── menus.py
│   └── platos.py
├── templates/            # Plantillas HTML
│   ├── base.html
│   ├── albaranes/
│   ├── clientes/
│   ├── cuadro_mando/
│   ├── importar/
│   ├── ingredientes/
│   ├── menus/
│   └── platos/
├── static/               # Archivos estáticos
│   ├── css/
│   └── js/
├── utils/                # Utilidades
│   └── stock_manager.py
├── crear_usuarios.py     # Script de gestión de usuarios
└── requirements.txt      # Dependencias
```

## 🚀 Instalación y Uso

### Requisitos Previos
- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### Instalación
```bash
# Clonar el repositorio
git clone [repository-url]
cd alabaranes-unei2

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Crear usuarios del sistema
python crear_usuarios.py

# Ejecutar la aplicación
python app.py
```

### Acceso
- **URL**: http://localhost:5000
- **Puerto**: 5000 (configurable)
- **Host**: 0.0.0.0 (accesible desde la red local)

### Credenciales de Prueba
- **Usuario**: admin
- **Contraseña**: admin123

*Nota: Es recomendable cambiar estas credenciales en producción*

## ⚙️ Configuración

### Modo Debug
Para habilitar el modo debug (desactiva validaciones de stock):
```python
# En config.py
DEBUG_MODE = True
```

### Base de Datos
La aplicación utiliza SQLite por defecto. La base de datos se crea automáticamente en `database/database.db`.

### Datos de Ejemplo
Ejecutar `load_sample_data.py` para cargar datos de prueba:
```bash
python load_sample_data.py
```

## 📈 Características Avanzadas

### Trazabilidad
- **Seguimiento completo** desde ingredientes hasta entrega
- **Registro de lotes** en cada movimiento de stock
- **Historial detallado** de todas las operaciones

### Control de Stock
- **Validaciones automáticas** antes de producción
- **Alertas de stock insuficiente**
- **Movimientos de stock** registrados automáticamente

### Reportes
- **Exportación CSV** de todos los módulos
- **Formato Excel** compatible con BOM UTF-8
- **Datos filtrados** por fechas y criterios específicos

### Interfaz de Usuario
- **Responsive Design** adaptable a dispositivos móviles
- **Búsqueda en tiempo real** en todas las tablas
- **Paginación automática** para grandes volúmenes de datos
- **Feedback visual** con mensajes de estado

## 🛠️ Desarrollo y Mantenimiento

### Logs y Debugging
- Sistema de logs integrado
- Modo debug configurable
- Manejo de excepciones detallado

### Escalabilidad
- Arquitectura modular preparada para crecimiento
- Base de datos relacional optimizada
- APIs REST para integraciones futuras

### Seguridad
- **Sistema de Autenticación**: Login obligatorio para todas las funcionalidades
- **Contraseñas Seguras**: Hash con Werkzeug para protección de credenciales
- **Gestión de Sesiones**: Control seguro con Flask-Login
- **Validación de Datos**: Control en servidor y cliente
- **Protección SQL**: Prevención de inyección mediante ORM
- **Manejo de Archivos**: Procesamiento seguro de CSV

---

*Desarrollado para la gestión eficiente de cocinas industriales con enfoque en trazabilidad y control de calidad.*