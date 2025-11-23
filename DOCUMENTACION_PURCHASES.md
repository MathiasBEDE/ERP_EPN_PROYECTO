# 🛒 Módulo de Compras (Purchases)

## Descripción General
Módulo encargado de la gestión completa del ciclo de compras, desde la creación de órdenes de compra hasta la recepción de materiales, con integración automática a inventario y contabilidad.

---

## Modelos Principales

### 1. **OrderStatus** (Estado de Orden)
Define los estados posibles de las órdenes de compra (y venta).

**Campos:**
- `name`: Nombre descriptivo del estado - CharField(100, unique=True)
- `symbol`: Símbolo único identificador - CharField(10, unique=True)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, SET_NULL, null=True)

**Métodos:**
- `__str__()`: Retorna formato "Name (Symbol)"
  ```python
  def __str__(self):
      return f"{self.name} ({self.symbol})"
  ```

**Tabla de Base de Datos:** `order_status`

**Estados Estándar del Sistema:**
- `DRAFT` - Draft: Borrador, en edición
- `CONFIRMED` - Confirmed: Confirmada, pendiente de recepción
- `RECEIVED` - Fully Received: Completamente recibida
- `CLOSED` - Closed: Cerrada administrativamente
- `CANCELLED` - Cancelled: Cancelada

**Flujo de Estados:**
```
DRAFT → CONFIRMED → RECEIVED → CLOSED
  ↓         ↓
CANCELLED  CANCELLED
```

---

### 2. **PurchaseOrder** (Orden de Compra)
Representa una orden de compra a un proveedor.

**Campos:**
- `id_purchase_order`: Código único (ej: PO-0001) - CharField(50, unique=True)
- `supplier`: Proveedor - ForeignKey(Supplier, PROTECT)
- `issue_date`: Fecha de emisión - DateField
- `estimated_delivery_date`: Fecha estimada de entrega - DateField
- `status`: Estado de la orden - ForeignKey(OrderStatus, PROTECT)
- `destination_location`: Ubicación de destino del inventario - ForeignKey(InventoryLocation, SET_NULL, null=True)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, SET_NULL, null=True)

**Métodos:**
- `__str__()`: Retorna formato "ID - Supplier Name"
  ```python
  def __str__(self):
      return f"{self.id_purchase_order} - {self.supplier.name}"
  ```

- `get_total_amount()`: Calcula el monto total de la orden
  ```python
  def get_total_amount(self):
      """
      Calcula el monto total sumando precio × cantidad de todas las líneas.
      Returns: Decimal con el total o 0 si no hay líneas
      """
      total = self.lines.aggregate(
          total=Sum(F('price') * F('quantity'), output_field=models.DecimalField())
      )['total']
      return total if total is not None else 0
  ```

**Tabla de Base de Datos:** `purchase_order`

**Related Names:**
- `lines`: Acceso a las líneas de la orden (PurchaseOrderLine)
- `purchase_orders` (desde InventoryLocation): Órdenes con esta ubicación de destino

---

### 3. **PurchaseOrderLine** (Línea de Orden de Compra)
Detalle de materiales incluidos en cada orden de compra.

**Campos:**
- `id_purchase_order_line`: Código único (ej: PO-0001-L001) - CharField(50, unique=True)
- `purchase_order`: Orden de compra padre - ForeignKey(PurchaseOrder, CASCADE)
- `material`: Material a comprar - ForeignKey(Material, PROTECT)
- `position`: Posición/orden de la línea - IntegerField
- `quantity`: Cantidad solicitada - IntegerField
- `unit_material`: Unidad de medida - ForeignKey(Unit, PROTECT)
- `price`: Precio unitario - DecimalField(10, 2)
- `currency_supplier`: Moneda del precio - ForeignKey(Currency, PROTECT)
- `received_quantity`: Cantidad ya recibida - IntegerField(default=0)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, SET_NULL, null=True)

**Métodos:**
- `__str__()`: Retorna formato "Line ID - Material Name"
  ```python
  def __str__(self):
      return f"{self.id_purchase_order_line} - {self.material.name}"
  ```

**Tabla de Base de Datos:** `lines_purchase_order`

**Validaciones:**
- `quantity` debe ser > 0
- `price` debe ser ≥ 0
- `received_quantity` debe ser ≥ 0
- `received_quantity` no debe exceder `quantity`

**Cálculos:**
- Total de línea: `quantity × price`
- Cantidad pendiente: `quantity - received_quantity`
- Estado: Parcialmente recibida si `0 < received_quantity < quantity`

---

## URLs Disponibles

```python
# Vistas HTML
/purchases/purchase-order/                    # Lista de órdenes de compra
/purchases/purchase-order/new/                # Formulario crear orden
/purchases/purchase-order/<order_id>/         # Detalle de orden

# APIs JSON
/purchases/api/supplier/details/<supplier_id>/  # Detalles de proveedor
/purchases/api/material/details/<material_id>/  # Detalles de material
/purchases/api/purchase-order/create/           # Crear orden (POST JSON)
```

---

## Vistas (Views)

### 1. **purchase_order_list_view**
Lista paginada de órdenes de compra con filtros y exportación CSV.

**URL:** `/purchases/purchase-order/`  
**Método:** GET  
**Decorador:** Ninguno (pública o requiere login según settings)

**Parámetros GET (Filtros):**
- `q`: Buscar por ID de orden o nombre de proveedor (icontains)
- `supplier`: Filtrar por ID de proveedor (id_supplier field)
- `status`: Filtrar por símbolo de estado (ej: DRAFT, CONFIRMED)
- `date_from`: Fecha de emisión desde (YYYY-MM-DD)
- `date_to`: Fecha de emisión hasta (YYYY-MM-DD)
- `page`: Número de página (paginación de 10 registros)
- `export`: Si es "csv", exporta resultados filtrados

**Funcionalidades:**
- ✅ Paginación (10 órdenes por página)
- ✅ Filtros combinables
- ✅ Búsqueda por texto
- ✅ Exportación CSV con UTF-8 BOM
- ✅ Optimización con select_related()

**Exportación CSV:**
- Content-Type: `text/csv; charset=utf-8`
- Filename: `ordenes_compra.csv`
- Separador: coma (,)
- Encoding: UTF-8 con BOM (\ufeff)
- Columnas:
  - ID Orden
  - Proveedor ID
  - Proveedor Nombre
  - Estado
  - Fecha Emisión
  - Fecha Estimada Entrega
  - Total Orden (USD)
  - Creado Por
  - Fecha Creación

**Contexto del Template:**
```python
{
    'page_obj': <Page object>,
    'orders': <lista de órdenes en página actual>,
    'statuses': <todos los estados>,
    'suppliers': <todos los proveedores>,
    'filters': {filtros aplicados},
    'total_count': <total de registros>
}
```

**Ejemplos de uso:**
```
# Todas las órdenes
/purchases/purchase-order/

# Órdenes en borrador
/purchases/purchase-order/?status=DRAFT

# Órdenes de un proveedor
/purchases/purchase-order/?supplier=SUP-001

# Búsqueda por texto
/purchases/purchase-order/?q=acero

# Rango de fechas
/purchases/purchase-order/?date_from=2024-01-01&date_to=2024-12-31

# Exportar filtrado
/purchases/purchase-order/?status=CONFIRMED&export=csv
```

---

### 2. **purchase_order_detail_view**
Vista de detalle completo de una orden con acciones de estado.

**URL:** `/purchases/purchase-order/<order_id>/`  
**Método:** GET, POST  
**Parámetro:** `order_id` es el código único (ej: PO-0001)

**Acciones POST:**
- `receive`: Marcar como recibida (DRAFT/CONFIRMED → RECEIVED)
- `cancel`: Cancelar orden (DRAFT/CONFIRMED → CANCELLED)
- `close`: Cerrar administrativamente (RECEIVED → CLOSED)

**Proceso al RECIBIR (action=receive):**

1. **Validaciones:**
   - Estado debe ser DRAFT o CONFIRMED
   - Si no cumple, muestra error y redirige

2. **Actualización de cantidades:**
   ```python
   for line in order.lines.all():
       line.received_quantity = line.quantity
       line.save()
   ```

3. **Cambio de estado:**
   ```python
   order.status = OrderStatus.objects.get(symbol='RECEIVED')
   order.save()
   ```

4. **Crear movimientos de inventario:**
   ```python
   created_movements = create_inventory_movements_for_purchase_order(
       order, 
       user=request.user
   )
   ```
   - Se crean movimientos tipo `PURCHASE_IN`
   - Incrementa stock en `destination_location`
   - Un movimiento por cada línea de la orden

5. **Crear asiento contable automático:**
   ```python
   journal_entry = create_entry_for_purchase(order, user=request.user)
   ```
   - Genera asiento contable automático
   - Débito: Inventario (Activo)
   - Crédito: Cuentas por Pagar (Pasivo)
   - Monto: Total de la orden

6. **Mensajes al usuario:**
   - ✅ Success: "Orden PO-XXXX marcada como recibida. Se crearon X movimiento(s) de inventario."
   - ✅ Success: "Asiento contable XXX generado automáticamente."
   - ⚠️ Warning: Si falla la contabilidad pero inventario se actualiza
   - ❌ Error: Si faltan datos de configuración (ubicaciones, tipos de movimiento)

**Proceso al CANCELAR (action=cancel):**
- Validación: Estado debe ser DRAFT o CONFIRMED
- Cambio de estado a CANCELLED
- No genera movimientos ni asientos
- Success: "Orden PO-XXXX cancelada exitosamente."

**Proceso al CERRAR (action=close):**
- Validación: Estado debe ser RECEIVED
- Cambio de estado a CLOSED
- No genera movimientos adicionales
- Success: "Orden PO-XXXX cerrada exitosamente."

**Acciones Disponibles por Estado:**
```python
available_actions = {
    'can_receive': order.status.symbol in ['DRAFT', 'CONFIRMED'],
    'can_cancel': order.status.symbol in ['DRAFT', 'CONFIRMED'],
    'can_close': order.status.symbol == 'RECEIVED',
}
```

**Contexto del Template:**
```python
{
    'order': <PurchaseOrder>,
    'available_actions': <dict de acciones disponibles>
}
```

**Manejo de Errores:**
- Http404: Si la orden no existe
- ValidationError: En contabilidad (no detiene transacción)
- InventoryLocation.DoesNotExist: Sin ubicaciones configuradas
- MovementType.DoesNotExist: Sin tipo PURCHASE_IN configurado

---

### 3. **purchase_order_form_view**
Formulario HTML para crear nueva orden de compra.

**URL:** `/purchases/purchase-order/new/`  
**Método:** GET  
**Decorador:** Ninguno

**Contexto del Template:**
```python
{
    'currencies': <todas las monedas ordenadas por code>,
    'locations': <ubicaciones activas ordenadas por name>,
    'today': <fecha actual en formato YYYY-MM-DD>
}
```

**Flujo:**
1. Muestra formulario con campos vacíos
2. Datos se envían vía JavaScript a API `create_purchase_order_api`
3. Frontend gestiona la creación dinámica de líneas
4. Submit envía JSON a `/purchases/api/purchase-order/create/`

---

### 4. **supplier_detail_api**
API que retorna detalles de un proveedor en JSON.

**URL:** `/purchases/api/supplier/details/<supplier_id>/`  
**Método:** GET  
**Parámetro:** `supplier_id` puede ser PK numérico o `id_supplier` (ej: SUP-001)

**Respuesta Exitosa (200):**
```json
{
    "supplier_id": 1,
    "id_supplier": "SUP-001",
    "name": "Proveedor XYZ",
    "address": "Calle 123",
    "city": "Santiago",
    "state_province": "Región Metropolitana",
    "country": "Chile",
    "postal_code": "1234567",
    "phone": "+56 2 2345 6789",
    "email": "contacto@proveedor.com",
    "contact_person": "Juan Pérez",
    "tax_id": "76.123.456-7",
    "payment_method": "Transferencia"
}
```

**Respuesta Error (404):**
```json
{"error": "Proveedor no encontrado"}
```

**Lógica de búsqueda:**
1. Intenta buscar por `id_supplier` (código ERP)
2. Si falla, intenta por PK numérico
3. Si ambos fallan, retorna 404

---

### 5. **material_detail_api**
API que retorna detalles de un material en JSON.

**URL:** `/purchases/api/material/details/<material_id>/`  
**Método:** GET  
**Parámetro:** `material_id` puede ser PK numérico o `id_material` (ej: MP-105)

**Respuesta Exitosa (200):**
```json
{
    "material_id": 1,
    "id_material": "MP-105",
    "name": "Acero Inoxidable 304",
    "description": "Lámina de acero inoxidable calibre 20",
    "material_code": "MP-105",
    "default_unit": "Kilogramo",
    "default_unit_id": 1,
    "material_type": "Raw material",
    "status": "Active"
}
```

**Respuesta Error (404):**
```json
{"error": "Material not found"}
```

**Lógica de búsqueda:**
1. Intenta buscar por `id_material` (código ERP)
2. Si falla, intenta por PK numérico
3. Si ambos fallan, retorna 404

---

### 6. **create_purchase_order_api**
API para crear orden de compra con sus líneas (JSON).

**URL:** `/purchases/api/purchase-order/create/`  
**Método:** POST  
**Content-Type:** `application/json`  
**Decoradores:** `@csrf_exempt`, `@transaction.atomic`

**Payload JSON Esperado:**
```json
{
    "supplier_id": 1,
    "estimated_delivery_date": "2024-12-31",
    "destination_location_id": 1,
    "lines": [
        {
            "material_id": "MP-105",
            "quantity": 100,
            "unit_id": 1,
            "price": 25.50,
            "currency_id": 1
        },
        {
            "material_id": 2,
            "quantity": 50,
            "unit_id": 2,
            "price": 10.00,
            "currency_id": 1
        }
    ]
}
```

**Campos Requeridos:**
- `supplier_id`: ID del proveedor (int)
- `estimated_delivery_date`: Fecha estimada (string YYYY-MM-DD)
- `lines`: Array de líneas (mínimo 1)

**Campos Opcionales:**
- `destination_location_id`: ID de ubicación de destino (int)

**Campos Requeridos por Línea:**
- `material_id`: ID o código del material (int o string)
- `quantity`: Cantidad (int > 0)
- `unit_id`: ID de unidad de medida (int)
- `price`: Precio unitario (decimal ≥ 0)
- `currency_id`: ID de moneda (int)

**Proceso de Creación:**

1. **Validar método POST**
2. **Parsear JSON del body**
3. **Validar campos requeridos:**
   - supplier_id presente
   - estimated_delivery_date presente
   - lines no vacío

4. **Validar proveedor existe:**
   ```python
   supplier = Supplier.objects.get(id=supplier_id)
   ```

5. **Validar ubicación (si se proporciona):**
   ```python
   destination_location = InventoryLocation.objects.get(id=destination_location_id)
   ```

6. **Obtener estado DRAFT:**
   ```python
   default_status = OrderStatus.objects.get(symbol='DRAFT')
   ```

7. **Generar ID único de orden:**
   ```python
   last_order = PurchaseOrder.objects.order_by('-id').first()
   last_number = int(last_order.id_purchase_order.split('-')[-1])
   new_purchase_order_id = f"PO-{(last_number + 1):04d}"
   ```
   Ejemplo: Si el último es PO-0005, genera PO-0006

8. **Crear PurchaseOrder:**
   ```python
   purchase_order = PurchaseOrder.objects.create(
       id_purchase_order=new_purchase_order_id,
       supplier=supplier,
       issue_date=date.today(),
       estimated_delivery_date=estimated_delivery_date,
       status=default_status,
       destination_location=destination_location,
       created_by=request.user if request.user.is_authenticated else None
   )
   ```

9. **Validar y crear líneas:**
   - Para cada línea en el array:
   - Validar campos requeridos
   - Validar rangos (quantity > 0, price ≥ 0)
   - Buscar material (intenta por código, luego por PK)
   - Validar unit existe
   - Validar currency existe
   - Generar ID de línea: `PO-XXXX-LYYY`
   - Crear PurchaseOrderLine

**Respuesta Exitosa (200):**
```json
{
    "message": "Purchase order created successfully",
    "id_purchase_order": "PO-0006",
    "purchase_order_id": "PO-0006",
    "lines_created": 2
}
```

**Respuestas de Error:**

**400 - Campos Faltantes:**
```json
{"error": "supplier_id is required"}
{"error": "estimated_delivery_date is required"}
{"error": "At least one line item is required"}
```

**400 - Validación de Líneas:**
```json
{"error": "Line 1: material_id is required"}
{"error": "Line 2: quantity must be greater than 0"}
{"error": "Line 3: price must be 0 or greater"}
{"error": "Line 1: Material not found (MP-999)"}
{"error": "Line 2: Unit with id 99 does not exist"}
```

**400 - Entidad No Encontrada:**
```json
{"error": "Supplier with id 999 does not exist"}
{"error": "Location with id 99 does not exist"}
{"error": "Estado \"DRAFT\" no encontrado..."}
```

**400 - JSON Inválido:**
```json
{"error": "Invalid JSON format"}
```

**405 - Método No Permitido:**
```json
{"error": "Method not allowed"}
```

**500 - Error Interno:**
```json
{"error": "Internal server error: <mensaje>"}
```

**Transaccionalidad:**
- Usa `@transaction.atomic`
- Si falla cualquier validación o creación, hace rollback completo
- Garantiza que no se creen órdenes incompletas

---

## Flujo de Trabajo Completo

### 1. Crear Orden de Compra

**Opción A: Interfaz Web**

1. Acceder a `/purchases/purchase-order/new/`
2. Completar formulario:
   - Seleccionar proveedor
   - Ingresar fecha estimada de entrega
   - Seleccionar ubicación de destino (opcional)
3. Agregar líneas de productos:
   - Buscar y seleccionar material
   - Ingresar cantidad
   - Seleccionar unidad
   - Ingresar precio unitario
   - Seleccionar moneda
4. JavaScript envía POST JSON a API
5. Sistema genera PO-XXXX automáticamente
6. Estado inicial: DRAFT
7. Redirige a detalle de orden creada

**Opción B: API Directa**

```python
import requests
import json

url = "http://localhost:8000/purchases/api/purchase-order/create/"
headers = {"Content-Type": "application/json"}

data = {
    "supplier_id": 1,
    "estimated_delivery_date": "2024-12-31",
    "destination_location_id": 1,
    "lines": [
        {
            "material_id": "MP-105",
            "quantity": 100,
            "unit_id": 1,
            "price": 25.50,
            "currency_id": 1
        }
    ]
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
# {'message': 'Purchase order created successfully', 'id_purchase_order': 'PO-0001'}
```

---

### 2. Confirmar Orden

**Cambio Manual de Estado:**
1. Acceder a detalle de orden: `/purchases/purchase-order/PO-0001/`
2. Desde admin o código: Cambiar estado a CONFIRMED
3. Orden queda confirmada, lista para recibir

**Estado:** DRAFT → CONFIRMED

---

### 3. Recibir Materiales

**Proceso Completo:**

1. Acceder a detalle de orden: `/purchases/purchase-order/PO-0001/`
2. Verificar que estado es DRAFT o CONFIRMED
3. Click en botón "Recibir Orden" (POST action=receive)
4. Sistema ejecuta automáticamente:

   **a) Actualizar cantidades recibidas:**
   ```python
   PO-0001-L001: received_quantity = 100 (era 0)
   PO-0001-L002: received_quantity = 50 (era 0)
   ```

   **b) Cambiar estado:**
   ```python
   Estado: CONFIRMED → RECEIVED
   ```

   **c) Crear movimientos de inventario:**
   ```python
   Movimiento 1:
     - Tipo: PURCHASE_IN
     - Material: MP-105
     - Cantidad: +100
     - Ubicación: BOD-01
     - Referencia: PO-0001
   
   Movimiento 2:
     - Tipo: PURCHASE_IN
     - Material: MP-110
     - Cantidad: +50
     - Ubicación: BOD-01
     - Referencia: PO-0001
   ```

   **d) Crear asiento contable:**
   ```python
   Asiento: JE-XXXX
   Descripción: "Compra de materiales - PO-0001"
   Fecha: 2024-11-23
   
   Líneas:
     Débito:  Inventario (Activo)        $2,550.00
     Crédito: Cuentas por Pagar (Pasivo) $2,550.00
   ```

5. Mensajes de confirmación:
   - ✅ "Orden PO-0001 marcada como recibida"
   - ✅ "Se crearon 2 movimiento(s) de inventario"
   - ✅ "Asiento contable JE-XXXX generado"

**Estado:** CONFIRMED → RECEIVED

---

### 4. Cerrar Orden Administrativamente

1. Acceder a detalle de orden recibida
2. Verificar que estado es RECEIVED
3. Click en "Cerrar Orden" (POST action=close)
4. Estado cambia a CLOSED
5. Orden queda archivada

**Estado:** RECEIVED → CLOSED

---

### 5. Cancelar Orden

**Antes de Recibir:**
1. Acceder a detalle de orden
2. Verificar que estado es DRAFT o CONFIRMED
3. Click en "Cancelar Orden" (POST action=cancel)
4. Estado cambia a CANCELLED
5. No se generan movimientos ni asientos

**Estado:** DRAFT/CONFIRMED → CANCELLED

⚠️ **Nota:** No se pueden cancelar órdenes RECEIVED o CLOSED

---

## Integraciones con Otros Módulos

### **Suppliers (Proveedores)**
- `PurchaseOrder.supplier`: FK a Supplier
- Validación: Proveedor debe existir y estar activo
- Datos del proveedor se usan en reportes y documentos

### **Materials (Materiales)**
- `PurchaseOrderLine.material`: FK a Material
- Validación: Material debe existir
- Unidad y precio por línea

### **Inventory (Inventario)**
- **Función:** `create_inventory_movements_for_purchase_order(order, user)`
- **Cuando:** Al recibir orden (RECEIVED)
- **Qué hace:**
  - Crea movimientos tipo PURCHASE_IN
  - Incrementa stock en destination_location
  - Un movimiento por cada línea
- **Referencia:** id_purchase_order en movimiento

### **Accounting (Contabilidad)**
- **Función:** `create_entry_for_purchase(order, user)`
- **Cuando:** Al recibir orden (RECEIVED)
- **Qué hace:**
  - Crea asiento contable automático
  - Débito: Inventario (Activo)
  - Crédito: Cuentas por Pagar (Pasivo)
  - Monto: Total de la orden
- **Descripción:** "Compra de materiales - PO-XXXX"

### **Core**
- Usa `Currency` para monedas
- Usa `Status` (indirectamente vía OrderStatus)

### **Users**
- `created_by`: Usuario que creó la orden
- Control de permisos para acciones

---

## Reglas de Negocio

### 1. **Numeración Automática**
- Sistema genera IDs únicos: PO-0001, PO-0002, etc.
- Formato: `PO-{número:04d}`
- Secuencial e incremental
- Líneas: `{id_purchase_order}-L{position:03d}`

### 2. **Estados y Transiciones Permitidas**

**Desde DRAFT:**
- ✅ CONFIRMED (confirmación manual)
- ✅ RECEIVED (recepción directa)
- ✅ CANCELLED (cancelación)

**Desde CONFIRMED:**
- ✅ RECEIVED (recepción)
- ✅ CANCELLED (cancelación)

**Desde RECEIVED:**
- ✅ CLOSED (cierre administrativo)
- ❌ No se puede cancelar ni volver atrás

**Desde CLOSED:**
- ❌ Estado final, no permite cambios

**Desde CANCELLED:**
- ❌ Estado final, no permite cambios

### 3. **Validaciones de Cantidades**
- `quantity` en línea debe ser > 0
- `price` en línea debe ser ≥ 0
- `received_quantity` se inicializa en 0
- Al recibir: `received_quantity = quantity`

### 4. **Integridad Referencial**
- `supplier`: PROTECT (no se puede eliminar proveedor en uso)
- `material`: PROTECT (no se puede eliminar material en uso)
- `status`: PROTECT (no se puede eliminar estado en uso)
- `unit_material`: PROTECT (no se puede eliminar unidad en uso)
- `currency_supplier`: PROTECT (no se puede eliminar moneda en uso)
- `purchase_order` en líneas: CASCADE (eliminar orden elimina líneas)

### 5. **Ubicación de Destino**
- Campo opcional al crear orden
- Requerido para crear movimientos de inventario
- Si no existe, inventario usa ubicación por defecto
- Puede ser null

### 6. **Auditoría**
- Todos los modelos tienen `created_at`, `updated_at`
- Registro de usuario creador (`created_by`)
- Timestamps automáticos

---

## Ejemplos de Código

### Crear Orden Programáticamente:
```python
from purchases.models import PurchaseOrder, PurchaseOrderLine, OrderStatus
from suppliers.models import Supplier
from materials.models import Material, Unit
from core.models import Currency
from inventory.models import InventoryLocation
from datetime import date, timedelta
from decimal import Decimal

# Obtener referencias
proveedor = Supplier.objects.get(id_supplier='SUP-001')
estado_draft = OrderStatus.objects.get(symbol='DRAFT')
ubicacion = InventoryLocation.objects.get(code='BOD-01')

# Crear orden
orden = PurchaseOrder.objects.create(
    id_purchase_order='PO-0001',
    supplier=proveedor,
    issue_date=date.today(),
    estimated_delivery_date=date.today() + timedelta(days=15),
    status=estado_draft,
    destination_location=ubicacion,
    created_by=request.user
)

# Agregar líneas
material1 = Material.objects.get(id_material='MP-105')
unidad_kg = Unit.objects.get(symbol='kg')
moneda_usd = Currency.objects.get(code='USD')

PurchaseOrderLine.objects.create(
    id_purchase_order_line='PO-0001-L001',
    purchase_order=orden,
    material=material1,
    position=1,
    quantity=100,
    unit_material=unidad_kg,
    price=Decimal('25.50'),
    currency_supplier=moneda_usd,
    received_quantity=0,
    created_by=request.user
)

print(f"Orden creada: {orden}")
print(f"Total: ${orden.get_total_amount():.2f}")
```

---

### Buscar y Filtrar Órdenes:
```python
from purchases.models import PurchaseOrder
from django.db.models import Q

# Todas las órdenes
todas = PurchaseOrder.objects.all()

# Órdenes en borrador
borradores = PurchaseOrder.objects.filter(status__symbol='DRAFT')

# Órdenes confirmadas
confirmadas = PurchaseOrder.objects.filter(status__symbol='CONFIRMED')

# Órdenes de un proveedor
proveedor = Supplier.objects.get(id_supplier='SUP-001')
ordenes_proveedor = PurchaseOrder.objects.filter(supplier=proveedor)

# Órdenes por rango de fechas
from datetime import date
hoy = date.today()
primer_dia_mes = hoy.replace(day=1)
ordenes_mes = PurchaseOrder.objects.filter(
    issue_date__gte=primer_dia_mes,
    issue_date__lte=hoy
)

# Buscar por texto (ID o proveedor)
busqueda = PurchaseOrder.objects.filter(
    Q(id_purchase_order__icontains='PO-') |
    Q(supplier__name__icontains='acero')
)

# Órdenes con destino específico
ubicacion = InventoryLocation.objects.get(code='BOD-01')
ordenes_ubicacion = PurchaseOrder.objects.filter(
    destination_location=ubicacion
)

# Ordenar por fecha de creación
recientes = PurchaseOrder.objects.all().order_by('-created_at')[:10]
```

---

### Calcular Totales y Estadísticas:
```python
from purchases.models import PurchaseOrder
from django.db.models import Sum, Count, Avg, F

# Total de todas las órdenes
total_general = sum(orden.get_total_amount() for orden in PurchaseOrder.objects.all())

# Órdenes por estado
por_estado = PurchaseOrder.objects.values('status__name').annotate(
    total=Count('id')
).order_by('-total')

for item in por_estado:
    print(f"{item['status__name']}: {item['total']}")

# Órdenes por proveedor
por_proveedor = PurchaseOrder.objects.values('supplier__name').annotate(
    total=Count('id'),
    monto_total=Sum(F('lines__price') * F('lines__quantity'))
).order_by('-monto_total')

# Total de líneas en una orden
orden = PurchaseOrder.objects.get(id_purchase_order='PO-0001')
num_lineas = orden.lines.count()
total_orden = orden.get_total_amount()

print(f"Orden {orden.id_purchase_order}:")
print(f"  - Líneas: {num_lineas}")
print(f"  - Total: ${total_orden:.2f}")
```

---

### Recibir Orden Manualmente:
```python
from purchases.models import PurchaseOrder, OrderStatus
from inventory.utils import create_inventory_movements_for_purchase_order
from accounting.utils import create_entry_for_purchase
from django.db import transaction

orden = PurchaseOrder.objects.get(id_purchase_order='PO-0001')

# Verificar estado
if orden.status.symbol not in ['DRAFT', 'CONFIRMED']:
    print(f"❌ No se puede recibir orden en estado {orden.status.name}")
else:
    with transaction.atomic():
        # Actualizar cantidades recibidas
        for line in orden.lines.all():
            line.received_quantity = line.quantity
            line.save()
        
        # Cambiar estado
        estado_received = OrderStatus.objects.get(symbol='RECEIVED')
        orden.status = estado_received
        orden.save()
        
        # Crear movimientos de inventario
        movimientos = create_inventory_movements_for_purchase_order(
            orden, 
            user=None  # o request.user
        )
        print(f"✅ Creados {len(movimientos)} movimientos de inventario")
        
        # Crear asiento contable
        try:
            asiento = create_entry_for_purchase(orden, user=None)
            print(f"✅ Asiento contable {asiento.id_journal_entry} creado")
        except Exception as e:
            print(f"⚠️ Error en contabilidad: {str(e)}")
        
        print(f"✅ Orden {orden.id_purchase_order} recibida exitosamente")
```

---

### Cancelar Orden:
```python
orden = PurchaseOrder.objects.get(id_purchase_order='PO-0002')

# Verificar estado
if orden.status.symbol not in ['DRAFT', 'CONFIRMED']:
    print(f"❌ No se puede cancelar orden en estado {orden.status.name}")
else:
    estado_cancelled = OrderStatus.objects.get(symbol='CANCELLED')
    orden.status = estado_cancelled
    orden.save()
    print(f"✅ Orden {orden.id_purchase_order} cancelada")
```

---

### Exportar Órdenes a CSV:
```python
import csv
from django.http import HttpResponse
from purchases.models import PurchaseOrder

def export_purchase_orders_csv(queryset):
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="purchase_orders.csv"'
    response.write('\ufeff')  # BOM para Excel
    
    writer = csv.writer(response)
    writer.writerow([
        'ID Orden', 'Proveedor', 'Estado', 'Fecha Emisión', 
        'Fecha Estimada', 'Total', 'Creado Por'
    ])
    
    for orden in queryset:
        writer.writerow([
            orden.id_purchase_order,
            orden.supplier.name,
            orden.status.name,
            orden.issue_date.strftime('%Y-%m-%d'),
            orden.estimated_delivery_date.strftime('%Y-%m-%d'),
            f'{orden.get_total_amount():.2f}',
            orden.created_by.username if orden.created_by else ''
        ])
    
    return response

# Uso
ordenes_mes = PurchaseOrder.objects.filter(
    issue_date__month=11,
    issue_date__year=2024
)
response = export_purchase_orders_csv(ordenes_mes)
```

---

## Notas Importantes

### ⚠️ **Advertencias:**

1. **No Eliminar Órdenes Recibidas:**
   - Pérdida de historial de inventario
   - Inconsistencia en contabilidad
   - Usar CANCELLED en su lugar

2. **Validar Estado Antes de Acciones:**
   - Cada acción tiene estados válidos
   - Sistema valida pero frontend debe prevenir

3. **Ubicación de Destino:**
   - Requerida para movimientos de inventario
   - Validar que existe y está activa
   - Configurar ubicaciones antes de recibir

4. **Tipos de Movimiento:**
   - Ejecutar `init_movement_types` antes de usar
   - PURCHASE_IN debe existir
   - Sin él, recepción falla

5. **Configuración Contable:**
   - Cuentas de Inventario y Cuentas por Pagar deben existir
   - País y moneda configurados
   - Si falla, orden se recibe pero sin asiento

6. **Transaccionalidad:**
   - create_purchase_order_api usa @transaction.atomic
   - Fallo en cualquier línea cancela toda la orden
   - Validar datos antes de enviar

---

### 💡 **Tips:**

1. **IDs Descriptivos:**
   - Usar prefijos claros: PO-XXXX
   - Mantener formato consistente
   - Facilita búsqueda y organización

2. **Fechas Realistas:**
   - `estimated_delivery_date` debe ser futura
   - Considerar tiempos de transporte
   - Alertas de órdenes vencidas

3. **Validación Frontend:**
   - Validar antes de enviar a API
   - Mostrar errores claros
   - Prevenir envíos inválidos

4. **Optimización de Queries:**
   - Usar `select_related()` para FKs
   - Usar `prefetch_related()` para líneas
   - Reducir consultas N+1

5. **Mensajes Claros:**
   - Informar al usuario cada acción
   - Distinguir success, warning, error
   - Incluir detalles relevantes

6. **Logging:**
   - Registrar operaciones importantes
   - Facilita debugging
   - Auditoría de acciones

---

### 📊 **Mejores Prácticas:**

1. **Flujo Completo:**
   - DRAFT: Crear y editar
   - CONFIRMED: Confirmar antes de recibir
   - RECEIVED: Recibir materiales
   - CLOSED: Cerrar administrativamente

2. **Control de Cambios:**
   - No editar órdenes RECEIVED o CLOSED
   - Cancelar en lugar de eliminar
   - Mantener historial intacto

3. **Revisión Antes de Recibir:**
   - Validar cantidades
   - Verificar precios
   - Confirmar proveedor y materiales

4. **Integración Automática:**
   - Aprovechar movimientos automáticos
   - Confiar en asientos contables automáticos
   - Validar pero no duplicar manualmente

5. **Reportes y Análisis:**
   - Exportar datos regularmente
   - Analizar por proveedor
   - Comparar precios históricos
   - Identificar órdenes pendientes

---

### 🔧 **Mantenimiento:**

1. **Órdenes Antiguas:**
   ```python
   # Cerrar órdenes recibidas hace más de 30 días
   from datetime import timedelta
   hace_30_dias = timezone.now() - timedelta(days=30)
   
   ordenes_antiguas = PurchaseOrder.objects.filter(
       status__symbol='RECEIVED',
       updated_at__lt=hace_30_dias
   )
   
   estado_closed = OrderStatus.objects.get(symbol='CLOSED')
   ordenes_antiguas.update(status=estado_closed)
   ```

2. **Auditoría de Estados:**
   ```python
   # Verificar órdenes sin estado
   sin_estado = PurchaseOrder.objects.filter(status__isnull=True)
   
   # Órdenes en DRAFT hace más de 60 días
   viejas_draft = PurchaseOrder.objects.filter(
       status__symbol='DRAFT',
       created_at__lt=timezone.now() - timedelta(days=60)
   )
   ```

3. **Limpieza de Datos:**
   ```python
   # Eliminar órdenes DRAFT sin líneas
   sin_lineas = PurchaseOrder.objects.annotate(
       num_lines=Count('lines')
   ).filter(num_lines=0, status__symbol='DRAFT')
   
   sin_lineas.delete()
   ```

4. **Validación de Integridad:**
   ```python
   # Órdenes RECEIVED sin movimientos de inventario
   from inventory.models import InventoryMovement
   
   recibidas = PurchaseOrder.objects.filter(status__symbol='RECEIVED')
   
   for orden in recibidas:
       movimientos = InventoryMovement.objects.filter(
           reference_document=orden.id_purchase_order
       )
       if not movimientos.exists():
           print(f"⚠️ Orden {orden.id_purchase_order} sin movimientos")
   ```

---

## Resumen Técnico

**Modelos:** 3 (OrderStatus, PurchaseOrder, PurchaseOrderLine)  
**Vistas:** 6 (list, detail, form, 3 APIs)  
**URLs:** 6  
**Métodos de Creación:** Web form + JSON API  
**Paginación:** 10 registros por página  
**Filtros:** 5 (búsqueda, proveedor, estado, fecha desde, fecha hasta)  
**Exportación:** CSV con UTF-8 BOM  
**Estados:** 5 (DRAFT, CONFIRMED, RECEIVED, CLOSED, CANCELLED)  
**Integraciones:** 4 (Suppliers, Materials, Inventory, Accounting)  
**Transaccionalidad:** Sí (@transaction.atomic en API)  

**Dependencias:**
- suppliers.Supplier
- materials.Material, Unit
- core.Currency
- inventory.InventoryLocation, utils
- accounting.utils
- users.User

**Funciones de Utilidad Externas:**
- `create_inventory_movements_for_purchase_order(order, user)` (inventory.utils)
- `create_entry_for_purchase(order, user)` (accounting.utils)
