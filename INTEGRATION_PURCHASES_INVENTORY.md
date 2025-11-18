# Integración Compras → Inventario

## Descripción General

El módulo de Compras está integrado con el módulo de Inventario para gestionar automáticamente el stock de materiales cuando se reciben órdenes de compra.

## Flujo de Integración

Cuando una orden de compra se marca como **"Fully Received"** (estado `RECEIVED`), el sistema automáticamente:

1. **Actualiza las cantidades recibidas** en todas las líneas de la orden
2. **Crea movimientos de entrada** en el inventario por cada línea
3. **Registra la referencia** a la orden de compra en cada movimiento
4. **Actualiza el stock** en la ubicación por defecto

## Componentes Involucrados

### Modelos

#### `PurchaseOrder` (purchases.models)
- Cabecera de la orden de compra
- Campo `status`: Estado actual de la orden
- Relación con `PurchaseOrderLine` a través de `related_name='lines'`

#### `PurchaseOrderLine` (purchases.models)
- Líneas de la orden de compra
- Campo `received_quantity`: Cantidad recibida del material
- Campo `quantity`: Cantidad original solicitada

#### `InventoryMovement` (inventory.models)
- Registro de movimientos de stock
- Campo `reference`: Referencia a la orden de compra (id_purchase_order)
- Campo `movement_date`: Fecha y hora del movimiento
- Campo `movement_type`: Tipo de movimiento (PURCHASE_IN)

#### `MovementType` (inventory.models)
- Tipos de movimiento de inventario
- Symbol `PURCHASE_IN`: Entrada por compra

#### `InventoryLocation` (inventory.models)
- Ubicaciones de almacén
- Campo `main_location`: Indica si es la ubicación principal

### Funciones Utilitarias (inventory/utils.py)

#### `get_default_inventory_location()`
```python
def get_default_inventory_location()
```
Obtiene la ubicación de inventario por defecto para recepciones.

**Retorna:**
- `InventoryLocation`: Ubicación marcada como `main_location=True`
- Si no hay ubicación principal, retorna la primera ubicación activa

**Excepciones:**
- `InventoryLocation.DoesNotExist`: Si no hay ubicaciones en el sistema

#### `create_inventory_movements_for_purchase_order(purchase_order, user=None)`
```python
def create_inventory_movements_for_purchase_order(purchase_order, user=None)
```
Crea movimientos de inventario para una orden de compra recibida.

**Parámetros:**
- `purchase_order`: Instancia de `PurchaseOrder` que ha sido recibida
- `user`: Usuario que ejecuta la acción (opcional)

**Retorna:**
- `list`: Lista de instancias de `InventoryMovement` creadas

**Características:**
- Usa `received_quantity` si está disponible, sino usa `quantity`
- Verifica duplicados antes de crear movimientos
- Usa transacción atómica para garantizar consistencia
- Salta líneas con cantidad cero

**Excepciones:**
- `InventoryLocation.DoesNotExist`: No hay ubicaciones configuradas
- `MovementType.DoesNotExist`: Tipo PURCHASE_IN no existe

### Vista de Detalle (purchases/views.py)

La vista `purchase_order_detail_view` maneja la acción de recibir órdenes:

```python
# Al ejecutar action='receive':
1. Valida que el estado sea DRAFT o CONFIRMED
2. Actualiza received_quantity en todas las líneas
3. Cambia el estado a RECEIVED
4. Llama a create_inventory_movements_for_purchase_order()
5. Muestra mensaje de éxito con número de movimientos creados
```

## Estados de Orden de Compra

| Estado | Símbolo | Descripción | Permite Recibir |
|--------|---------|-------------|-----------------|
| Draft | DRAFT | Borrador | ✓ |
| Confirmed | CONFIRMED | Confirmada | ✓ |
| Fully Received | RECEIVED | Recibida | ✗ |
| Cancelled | CANCELLED | Cancelada | ✗ |
| Closed | CLOSED | Cerrada | ✗ |
| Invoiced | INVOICED | Facturada | ✗ |

## Tipos de Movimiento de Inventario

| Nombre | Símbolo | Uso |
|--------|---------|-----|
| Entrada por Compra | PURCHASE_IN | Recepciones de órdenes de compra |
| Salida por Venta | SALE_OUT | Despachos de ventas |
| Ajuste Entrada | ADJUSTMENT_IN | Ajustes manuales positivos |
| Ajuste Salida | ADJUSTMENT_OUT | Ajustes manuales negativos |
| Transferencia Entrada | TRANSFER_IN | Recepción de transferencias |
| Transferencia Salida | TRANSFER_OUT | Envío de transferencias |

## Configuración Inicial

### 1. Ejecutar Migraciones

```bash
python manage.py migrate inventory
```

### 2. Inicializar Tipos de Movimiento

```bash
python manage.py init_movement_types
```

Este comando crea los 6 tipos de movimiento necesarios.

### 3. Inicializar Ubicación de Inventario

```bash
python manage.py init_inventory_location
```

Verifica que exista al menos una ubicación de inventario activa.

### 4. Verificar Estados de Orden

```bash
python manage.py init_order_statuses
```

Asegura que existan los estados DRAFT, CONFIRMED, RECEIVED, etc.

## Uso en la Aplicación

### Recibir una Orden de Compra

1. Navegar a **Dashboard → Compras**
2. Seleccionar una orden en estado **Draft** o **Confirmed**
3. Click en **"Ver"** para abrir el detalle
4. Click en botón **"Recibir Orden"** (verde)
5. Confirmar la acción

**Resultado:**
- Estado cambia a **"Fully Received"**
- `received_quantity` de cada línea = `quantity`
- Se crean movimientos de inventario automáticamente
- Mensaje de éxito: *"Orden PO-XXXX marcada como recibida. Se crearon N movimiento(s) de inventario."*

### Verificar Movimientos Creados

1. Ir al **Django Admin** → **Inventory** → **Inventory movements**
2. Buscar por la referencia de la orden (ej: `PO-0001`)
3. Ver detalles:
   - Material recibido
   - Cantidad
   - Ubicación
   - Tipo de movimiento (PURCHASE_IN)
   - Fecha y hora

## Protección contra Duplicados

La función `create_inventory_movements_for_purchase_order()` verifica si ya existen movimientos con:
- **reference** = `id_purchase_order`
- **movement_type** = `PURCHASE_IN`

Si existen, no crea movimientos duplicados y retorna lista vacía.

## Manejo de Errores

### Error: "No hay ubicaciones de inventario activas"

**Solución:**
```bash
python manage.py init_inventory_location
```

### Error: "Tipo de movimiento PURCHASE_IN no encontrado"

**Solución:**
```bash
python manage.py init_movement_types
```

### Error: "Estado DRAFT/RECEIVED no encontrado"

**Solución:**
```bash
python manage.py init_order_statuses
```

## Atomicidad de Transacciones

Todo el proceso de recepción está envuelto en una transacción atómica:

```python
with transaction.atomic():
    # 1. Actualizar cantidades recibidas
    # 2. Cambiar estado a RECEIVED
    # 3. Crear movimientos de inventario
```

Si **cualquier** paso falla, **toda** la operación se revierte.

## Pruebas

### Script de Prueba Automatizada

Ejecutar el script de prueba incluido:

```bash
python test_purchase_inventory_integration.py
```

**El script verifica:**
- ✓ Creación de orden de compra
- ✓ Cambio de estado a RECEIVED
- ✓ Creación de movimientos de inventario
- ✓ Protección contra duplicados
- ✓ Integridad de referencias

### Prueba Manual

1. Crear una orden de compra nueva
2. Agregar al menos 2 líneas con diferentes materiales
3. Guardar la orden (estado: Draft)
4. Abrir el detalle de la orden
5. Click en "Recibir Orden"
6. Verificar en Admin → Inventory movements que se crearon 2 movimientos
7. Intentar recibir la orden nuevamente (debería estar bloqueado)

## Consideraciones Futuras

### Recepciones Parciales

Actualmente, la recepción es **todo o nada**. Para implementar recepciones parciales:

1. Modificar la vista para aceptar cantidades específicas por línea
2. Actualizar solo `received_quantity` de líneas seleccionadas
3. Verificar si todas las líneas están recibidas antes de cambiar a RECEIVED
4. Crear un estado intermedio `PARTIALLY_RECEIVED`

### Integración con Facturación

Cuando el estado pase a `INVOICED`:
- Crear registros contables automáticamente
- Vincular con facturas de proveedor
- Actualizar cuentas por pagar

### Reportes de Stock

Con los movimientos de inventario registrados:
- Calcular stock actual por material
- Generar reportes de entrada/salida
- Alertas de stock mínimo
- Valorización de inventario

## Resumen de Integración

```
┌─────────────────────┐
│  Orden de Compra    │
│   (DRAFT/CONFIRMED) │
└──────────┬──────────┘
           │
           │ Usuario click "Recibir"
           ▼
┌──────────────────────────────────────┐
│  purchase_order_detail_view          │
│  - Actualiza received_quantity       │
│  - Cambia estado a RECEIVED          │
│  - Llama a create_inventory_movements│
└──────────┬───────────────────────────┘
           │
           ▼
┌─────────────────────────────────────┐
│  inventory/utils.py                 │
│  - get_default_inventory_location() │
│  - Crea InventoryMovement por línea │
│  - Tipo: PURCHASE_IN                │
│  - Reference: id_purchase_order     │
└──────────┬──────────────────────────┘
           │
           ▼
┌──────────────────────┐
│  Stock Actualizado   │
│  en Inventario       │
└──────────────────────┘
```

## Archivos Modificados/Creados

### Nuevos Archivos
- `inventory/utils.py` - Funciones utilitarias
- `inventory/management/commands/init_movement_types.py` - Inicializar tipos
- `inventory/management/commands/init_inventory_location.py` - Inicializar ubicaciones
- `test_purchase_inventory_integration.py` - Script de prueba

### Archivos Modificados
- `inventory/models.py` - Agregados campos `movement_date` y `reference`
- `purchases/views.py` - Integración en `purchase_order_detail_view`

### Migraciones
- `inventory/migrations/0002_inventorymovement_movement_date_and_more.py`

## Contacto y Soporte

Para dudas o problemas con la integración:
1. Revisar los logs de Django en la consola
2. Verificar que todos los comandos de inicialización se ejecutaron
3. Revisar el script de prueba para ejemplos de uso

---

**Última actualización:** Noviembre 17, 2025  
**Versión:** 1.0  
**Autor:** ERP Development Team
