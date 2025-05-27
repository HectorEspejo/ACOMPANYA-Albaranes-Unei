# Modo Debug - Sistema de Albaranes

## ¿Qué es el Modo Debug?

El modo debug es una funcionalidad especial que desactiva todas las verificaciones de stock en el sistema. Cuando está activado:

- Se pueden producir platos sin verificar si hay suficientes ingredientes
- Se pueden preparar menús sin verificar si hay suficientes platos
- Los stocks pueden quedar en números negativos
- Aparecerá un banner rojo en la parte superior indicando que el modo está activo

## ¿Cuándo usar el Modo Debug?

Este modo es útil para:
- Pruebas y desarrollo
- Demostraciones del sistema
- Situaciones de emergencia donde se necesita generar albaranes sin restricciones

⚠️ **ADVERTENCIA**: No usar en producción salvo casos excepcionales, ya que puede generar inconsistencias en los datos de stock.

## Cómo activar el Modo Debug

### Opción 1: Variable de entorno (Recomendado)

En Linux/Mac:
```bash
export DEBUG_MODE=true
python app.py
```

En Windows:
```cmd
set DEBUG_MODE=true
python app.py
```

### Opción 2: Archivo .env

Crear un archivo `.env` en la raíz del proyecto:
```
DEBUG_MODE=true
```

### Opción 3: Al ejecutar la aplicación

```bash
DEBUG_MODE=true python app.py
```

## Cómo desactivar el Modo Debug

Simplemente no definir la variable de entorno o establecerla en `false`:

```bash
export DEBUG_MODE=false
# o simplemente no definirla
unset DEBUG_MODE
```

## Indicadores visuales

Cuando el modo debug está activo:
- Aparece un banner rojo en la parte superior de todas las páginas
- En las pantallas de producción y preparación, los requisitos de stock siempre aparecerán como "suficientes"
- No se mostrarán errores de stock insuficiente

## Comportamiento del sistema en Modo Debug

### Producción de platos:
- No verifica si hay ingredientes suficientes
- Resta los ingredientes normalmente (puede resultar en stocks negativos)
- Incrementa el stock de platos producidos

### Preparación de menús:
- No verifica si hay platos suficientes
- Resta los platos normalmente (puede resultar en stocks negativos)
- Genera los albaranes sin restricciones

### Movimientos de stock:
- Se registran todos los movimientos normalmente
- Los stocks pueden quedar negativos
- La trazabilidad se mantiene intacta