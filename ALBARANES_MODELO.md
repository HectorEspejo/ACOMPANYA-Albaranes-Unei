# Albaranes Modelo - Sistema de Gestión

## ¿Qué son los Albaranes Modelo?

Los albaranes modelo son plantillas predefinidas que se crean para cada cliente, organizadas por:
- **Semana**: Del 1 al 4
- **Día de la semana**: Lunes a Domingo

Cada cliente tendrá un total de **28 albaranes modelo** (4 semanas × 7 días).

## Nomenclatura

Los albaranes modelo siguen esta estructura de referencia:
```
XX-00-NombreCliente
```

Donde:
- **XX**: Código del día de la semana
  - LU = Lunes
  - MA = Martes
  - MI = Miércoles
  - JU = Jueves
  - VI = Viernes
  - SA = Sábado
  - DO = Domingo
- **00**: Número de semana (01-04)
- **NombreCliente**: Nombre completo del cliente

### Ejemplos:
- `LU-01-UNEI Iniciativa Social S.L., Faisem Málaga ( C.D ARQUIMEDES )` → Lunes de la semana 1
- `VI-03-UNEI Iniciativa Social S.L., Faisem Málaga ( C.D MALASAÑA ,25 )` → Viernes de la semana 3

## Scripts de Gestión

### 1. Script Principal: `gestionar_albaranes_modelo.py`

Este script ofrece un menú interactivo con las siguientes opciones:

```bash
python gestionar_albaranes_modelo.py
```

**Opciones disponibles:**
1. **Crear albaranes modelo**: Genera los 28 albaranes para cada cliente
2. **Eliminar albaranes modelo vacíos**: Elimina solo los albaranes modelo que no tienen productos
3. **Ver estadísticas**: Muestra cuántos albaranes modelo hay y cuáles tienen productos
4. **Salir**

### 2. Script Simple: `crear_albaranes_modelo.py`

Script directo para crear albaranes modelo:

```bash
python crear_albaranes_modelo.py
```

## Uso Típico

### 1. Primera vez - Crear albaranes modelo:
```bash
# Asegúrate de haber importado los clientes primero
python gestionar_albaranes_modelo.py
# Selecciona opción 1
```

### 2. Ver estadísticas:
```bash
python gestionar_albaranes_modelo.py
# Selecciona opción 3
```

### 3. Limpiar albaranes modelo no utilizados:
```bash
python gestionar_albaranes_modelo.py
# Selecciona opción 2
```

## Características importantes

1. **Protección de datos**: Solo se eliminan albaranes modelo que NO tienen productos asociados
2. **Verificación**: El sistema verifica si ya existe un albarán antes de crear uno nuevo
3. **Referencias únicas**: No interfiere con las referencias automáticas de albaranes normales (formato YYYYMMDD-####)

## Flujo de trabajo recomendado

1. **Importar clientes** desde el archivo CSV
2. **Ejecutar el script** de creación de albaranes modelo
3. **Usar los albaranes modelo** para registrar entregas recurrentes
4. Los albaranes modelo aparecerán en la lista normal de albaranes
5. Puedes añadir productos a cualquier albarán modelo según necesites

## Notas técnicas

- Los albaranes modelo se crean con la fecha actual
- El campo destinatario incluye información completa: cliente, ciudad, semana y día
- Los albaranes normales siguen usando referencias automáticas (YYYYMMDD-####)
- Los albaranes modelo mantienen todas las funcionalidades: añadir productos, exportar, imprimir, etc.