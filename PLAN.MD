# Plan de Desarrollo - Sistema de Albaranes Acompanya

## Descripción del Proyecto
Sistema de gestión para empresa de cocina industrial que permite administrar ingredientes, platos, menús y generar albaranes con trazabilidad completa de lotes.

## Stack Tecnológico
- **Frontend**: HTML, CSS
- **Backend**: Python (Flask)
- **Base de Datos**: SQLite (base de datos interna)
- **ORM**: SQLAlchemy

## Arquitectura del Sistema

### 1. Estructura de la Base de Datos

#### Tabla: ingredientes
- id (INTEGER, PK)
- nombre (VARCHAR)
- tipo_unidad (ENUM: 'unidades', 'gramos', 'litros', 'mililitros')
- stock_actual (FLOAT)
- fecha_caducidad (DATE)
- lote (VARCHAR)
- es_plato (BOOLEAN) - Para ingredientes que también son platos
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

#### Tabla: platos
- id (INTEGER, PK)
- nombre (VARCHAR)
- lote_propio (VARCHAR)
- stock_actual (FLOAT)
- unidad (VARCHAR) - Tipo de unidad del plato
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

#### Tabla: platos_ingredientes (Relación N:M)
- id (INTEGER, PK)
- plato_id (INTEGER, FK)
- ingrediente_id (INTEGER, FK)
- cantidad (FLOAT)
- unidad (VARCHAR)

#### Tabla: menus
- id (INTEGER, PK)
- nombre (VARCHAR)
- dia_semana (ENUM: 'lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo')
- numero_semana (INTEGER)
- tipo_dieta (VARCHAR) - Ej: 'basal', 'diabética', etc.
- tipo_comida (ENUM: 'desayuno', 'almuerzo', 'cena', 'merienda')
- created_at (TIMESTAMP)

#### Tabla: menus_platos (Relación N:M)
- id (INTEGER, PK)
- menu_id (INTEGER, FK)
- plato_id (INTEGER, FK)
- cantidad (INTEGER)

#### Tabla: albaranes
- id (INTEGER, PK)
- fecha (DATE)
- referencia (VARCHAR) - Código único del albarán
- destinatario (VARCHAR)
- created_at (TIMESTAMP)

#### Tabla: albaranes_detalles
- id (INTEGER, PK)
- albaran_id (INTEGER, FK)
- menu_id (INTEGER, FK, nullable)
- plato_id (INTEGER, FK)
- cantidad_entregada (FLOAT)
- unidad (VARCHAR)
- lote (VARCHAR)

#### Tabla: movimientos_stock
- id (INTEGER, PK)
- tipo_movimiento (ENUM: 'entrada', 'salida', 'ajuste')
- entidad_tipo (ENUM: 'ingrediente', 'plato')
- entidad_id (INTEGER)
- cantidad (FLOAT)
- motivo (VARCHAR)
- referencia_documento (VARCHAR) - Ej: ID del albarán
- created_at (TIMESTAMP)

### 2. Pasos de Desarrollo

#### Fase 1: Configuración del Proyecto
1. Crear estructura de directorios:
   ```
   alabaranes-unei2/
   ├── app.py
   ├── config.py
   ├── requirements.txt
   ├── database/
   │   ├── __init__.py
   │   ├── models.py
   │   └── database.db
   ├── routes/
   │   ├── __init__.py
   │   ├── ingredientes.py
   │   ├── platos.py
   │   ├── menus.py
   │   └── albaranes.py
   ├── templates/
   │   ├── base.html
   │   ├── index.html
   │   ├── ingredientes/
   │   ├── platos/
   │   ├── menus/
   │   └── albaranes/
   ├── static/
   │   ├── css/
   │   │   └── style.css
   │   └── js/
   │       └── main.js
   └── utils/
       ├── __init__.py
       └── stock_manager.py
   ```

2. Instalar dependencias:
   - Flask
   - SQLAlchemy
   - Flask-SQLAlchemy
   - python-dateutil

#### Fase 2: Implementación de la Base de Datos
1. Definir modelos SQLAlchemy con todas las relaciones
2. Crear script de migración para inicializar la base de datos
3. Implementar funciones de validación de datos

#### Fase 3: Lógica de Negocio
1. **Gestión de Stock**:
   - Función para actualizar stock de ingredientes al crear platos
   - Función para actualizar stock de platos al crear menús
   - Sistema de alertas para stock bajo o caducidad próxima

2. **Trazabilidad de Lotes**:
   - Heredar lotes de ingredientes a platos
   - Heredar lotes de platos a menús
   - Mantener histórico de lotes en albaranes

3. **Generación de Albaranes**:
   - Agrupar por menús
   - Listar platos dentro de cada menú
   - Incluir información de lotes y cantidades

#### Fase 4: Interfaz de Usuario
1. **Formularios de entrada**:
   - Alta de ingredientes con validación
   - Creación de platos con selección de ingredientes
   - Composición de menús con platos disponibles
   - Generación de albaranes

2. **Vistas de consulta**:
   - Listado de ingredientes con stock y caducidad
   - Catálogo de platos con composición
   - Calendario de menús por semana
   - Histórico de albaranes

3. **Reportes**:
   - Vista previa e impresión de albaranes
   - Informes de stock
   - Trazabilidad de lotes

#### Fase 5: Funcionalidades Adicionales
1. Importación de datos desde CSV
2. Exportación de albaranes a PDF
3. Sistema de búsqueda y filtros
4. Dashboard con métricas principales

### 3. Consideraciones Técnicas

#### Validaciones Importantes
- No permitir stock negativo
- Verificar fechas de caducidad antes de usar ingredientes
- Validar que exista suficiente stock antes de crear platos/menús
- Asegurar integridad referencial en las relaciones

#### Optimizaciones
- Índices en campos de búsqueda frecuente (nombre, lote, fecha)
- Cache para consultas recurrentes
- Transacciones para operaciones múltiples de stock

#### Seguridad
- Validación de entrada de datos
- Escape de caracteres especiales en HTML
- Manejo seguro de sesiones
- Logs de auditoría para cambios críticos

### 4. Testing
1. Tests unitarios para lógica de negocio
2. Tests de integración para flujos completos
3. Validación con datos del archivo model.csv
4. Pruebas de rendimiento con volúmenes altos

### 5. Despliegue
1. Configuración de entorno de producción
2. Backup automático de base de datos
3. Documentación de usuario final
4. Manual de administración del sistema

## Cronograma Estimado
- Fase 1-2: 2 días
- Fase 3: 3 días
- Fase 4: 3 días
- Fase 5: 2 días
- Testing y ajustes: 2 días
- **Total: 12 días**