# 🛍️ Módulo de Ventas (Sales)

## Descripción General
Módulo encargado de la gestión completa del ciclo de ventas, desde la creación de órdenes de venta hasta la entrega de productos, con integración automática a inventario y contabilidad.

---

## Modelos Principales

### 1. **SalesOrder** (Orden de Venta)
Representa una orden de venta a un cliente.

**Campos:**
- `id_sales_order`: Código único (ej: SO-0001) - CharField(50, unique=True)
- `customer`: Cliente - ForeignKey(Customer, PROTECT)
- `issue_date`: Fecha de emisión - DateField
- `status`: Estado de la orden - ForeignKey(OrderStatus, PROTECT)
- `source_location`: Ubicación origen del inventario - ForeignKey(InventoryLocation, PROTECT, null=True)
- `notes`: Notas o comentarios adicionales - TextField(blank=True, null=True)
- `invoice_number`: Número de factura o referencia contable - CharField(50, null=True)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, SET_NULL, null=True)

**Métodos:**

- `__str__()`: Retorna formato "ID - Customer Name"
  ```python
  def __str__(self):
      return f"{self.id_sales_order} - {self.customer.name}"
  ```

- `get_total_amount()`: Calcula el monto total por moneda
  ```python
  def get_total_amount(self):
      """
      Calcula el monto total sumando todas las líneas.
      Retorna un diccionario con totales por moneda.
      Ej: {'USD': Decimal('1500.50'), 'EUR': Decimal('800.00')}
      """
      from decimal import Decimal
      from collections import defaultdict
      
      totals = defaultdict(Decimal)
      for line in self.lines.all():
          line_total = line.quantity * line.price
          currency_code = line.currency_customer.code
          totals[currency_code] += line_total
      
      return dict(totals)
  ```

- `get_delivery_status()`: Calcula el estado de entrega
  ```python
  def get_delivery_status(self):
      """
      Calcula el estado de entrega de la orden.
      Retorna: 'not_delivered', 'partially_delivered', 'fully_delivered'
      """
      lines = self.lines.all()
      if not lines:
          return 'not_delivered'
      
      total_ordered = sum(line.quantity for line in lines)
      total_delivered = sum(line.delivered_quantity for line in lines)
      
      if total_delivered == 0:
          return 'not_delivered'
      elif total_delivered < total_ordered:
          return 'partially_delivered'
      else:
          return 'fully_delivered'
  ```

**Tabla de Base de Datos:** `sales_order`

**Índices:**
- `id_sales_order` (búsqueda rápida)
- `customer` (órdenes por cliente)
- `status` (órdenes por estado)
- `-created_at` (órdenes más recientes primero)

**Related Names:**
- `lines`: Acceso a las líneas de la orden (SalesOrderLine)
- `sales_orders` (desde Customer): Órdenes del cliente
- `sales_orders` (desde OrderStatus): Órdenes con ese estado
- `sales_orders` (desde InventoryLocation): Órdenes desde esa ubicación

---

### 2. **SalesOrderLine** (Línea de Orden de Venta)
Detalle de materiales/productos en cada orden de venta.

**Campos:**
- `id_sales_order_line`: Código único (ej: SO-0001-L001) - CharField(50, unique=True)
- `sales_order`: Orden de venta padre - ForeignKey(SalesOrder, CASCADE)
- `material`: Material/producto vendido - ForeignKey(Material, PROTECT)
- `position`: Posición/secuencia de la línea - IntegerField
- `quantity`: Cantidad vendida - IntegerField
- `unit_material`: Unidad de medida - ForeignKey(Unit, PROTECT)
- `price`: Precio unitario de venta - DecimalField(10, 2)
- `currency_customer`: Moneda del precio - ForeignKey(Currency, PROTECT)
- `delivered_quantity`: Cantidad ya entregada - IntegerField(default=0)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, SET_NULL, null=True)

**Métodos:**

- `__str__()`: Retorna formato "Line ID - Material Name"
  ```python
  def __str__(self):
      return f"{self.id_sales_order_line} - {self.material.name}"
  ```

- `get_line_total()`: Calcula el total de la línea
  ```python
  def get_line_total(self):
      """Calcula el total de la línea (cantidad × precio)"""
      from decimal import Decimal
      return Decimal(self.quantity) * self.price
  ```

- `get_pending_quantity()`: Calcula cantidad pendiente
  ```python
  def get_pending_quantity(self):
      """Calcula la cantidad pendiente de entrega"""
      return max(0, self.quantity - self.delivered_quantity)
  ```

- `is_fully_delivered()`: Verifica si está completamente entregada
  ```python
  def is_fully_delivered(self):
      """Verifica si la línea ha sido completamente entregada"""
      return self.delivered_quantity >= self.quantity
  ```

**Tabla de Base de Datos:** `lines_sales_order`

**Índices:**
- `id_sales_order_line` (búsqueda rápida)
- `sales_order` (líneas de una orden)
- `material` (ventas de un material)

**Constraint Único:**
- `['sales_order', 'position']`: No pueden haber dos líneas con la misma posición en una orden

**Validaciones:**
- `quantity` debe ser > 0
- `price` debe ser ≥ 0
- `delivered_quantity` debe ser ≥ 0
- `delivered_quantity` no debe exceder `quantity`

---

## URLs Disponibles

```python
# Vistas HTML
/sales/sales-order/                    # Lista de órdenes de venta
/sales/sales-order/new/                # Formulario crear orden
/sales/sales-order/<order_id>/         # Detalle de orden
/sales/sales-order/<order_id>/edit/    # Editar orden (solo DRAFT)

# APIs JSON
/sales/api/customer/<customer_id>/     # Detalles de cliente
/sales/api/material/<material_id>/     # Detalles de material
/sales/api/create/                     # Crear orden (POST JSON)
```

---

## Vistas (Views)

### 1. **sales_order_list_view**
Lista paginada de órdenes de venta con filtros y exportación CSV.

**URL:** `/sales/sales-order/`  
**Método:** GET  
**Decorador:** Ninguno

**Parámetros GET (Filtros):**
- `q`: Buscar por ID de orden, nombre de cliente, o ID de cliente
- `customer`: Filtrar por ID de cliente (id_customer o pk)
- `status`: Filtrar por ID de estado
- `date_from`: Fecha de emisión desde (YYYY-MM-DD)
- `date_to`: Fecha de emisión hasta (YYYY-MM-DD)
- `page`: Número de página (paginación de 10 registros)
- `export`: Si es "csv", exporta resultados filtrados

**Funcionalidades:**
- ✅ Paginación (10 órdenes por página)
- ✅ Filtros combinables
- ✅ Búsqueda por texto múltiple
- ✅ Exportación CSV
- ✅ Optimización con select_related()

**Exportación CSV:**
- Content-Type: `text/csv`
- Filename: `sales_orders.csv`
- Separador: coma (,)
- Columnas:
  - ID Orden
  - Cliente
  - ID Cliente
  - Fecha Emisión
  - Estado
  - Ubicación Origen
  - Creado Por
  - Fecha Creación

**Contexto del Template:**
```python
{
    'page_obj': <Page object>,
    'sales_orders': <lista de órdenes en página actual>,
    'statuses': <todos los estados>,
    'customers': <clientes activos>,
    'search_query': <búsqueda aplicada>,
    'customer_filter': <filtro de cliente>,
    'status_filter': <filtro de estado>,
    'date_from': <fecha desde>,
    'date_to': <fecha hasta>
}
```

**Ejemplos de uso:**
```
# Todas las órdenes
/sales/sales-order/

# Órdenes en borrador
/sales/sales-order/?status=1

# Órdenes de un cliente
/sales/sales-order/?customer=CUST-001

# Búsqueda por texto
/sales/sales-order/?q=acme

# Rango de fechas
/sales/sales-order/?date_from=2024-01-01&date_to=2024-12-31

# Exportar filtrado
/sales/sales-order/?status=2&export=csv
```

---

### 2. **sales_order_create_view**
Formulario HTML para crear nueva orden de venta.

**URL:** `/sales/sales-order/new/`  
**Método:** GET  
**Decorador:** Ninguno

**Contexto del Template:**
```python
{
    'customers': <clientes activos ordenados por nombre>,
    'currencies': <todas las monedas ordenadas por code>,
    'locations': <ubicaciones activas ordenadas por code>,
    'materials': <materiales activos ordenados por id_material>,
    'units': <todas las unidades ordenadas por symbol>,
    'today': <fecha actual YYYY-MM-DD>
}
```

**Flujo:**
1. Muestra formulario con campos vacíos
2. Datos se envían vía JavaScript a API `create_sales_order_api`
3. Frontend gestiona la creación dinámica de líneas
4. Submit envía JSON a `/sales/api/create/`

---

### 3. **sales_order_edit_view**
Formulario para editar orden de venta existente (solo DRAFT).

**URL:** `/sales/sales-order/<order_id>/edit/`  
**Método:** GET  
**Parámetro:** `order_id` es el código único (ej: SO-0001)

**Validaciones:**
- Orden debe existir (404 si no existe)
- Estado debe ser DRAFT (redirige con error si no lo es)

**Contexto del Template:**
```python
{
    'order': <SalesOrder con sus líneas>,
    'currencies': <todas las monedas>,
    'locations': <ubicaciones activas>
}
```

**Mensajes de Error:**
- ❌ "No se puede editar una orden en estado 'Confirmed'. Solo órdenes en estado Draft pueden editarse."

---

### 4. **sales_order_detail_view**
Vista de detalle completo de una orden con acciones de estado.

**URL:** `/sales/sales-order/<order_id>/`  
**Método:** GET, POST  
**Parámetro:** `order_id` es el código único (ej: SO-0001)

**Acciones POST:**
- `confirm`: Confirmar orden (DRAFT → CONFIRMED)
- `deliver`: Entregar productos (CONFIRMED → DELIVERED)
- `cancel`: Cancelar orden (DRAFT/CONFIRMED → CANCELLED)

---

#### **Acción: CONFIRMAR (action=confirm)**

**Validaciones:**
- Estado debe ser DRAFT

**Proceso:**
1. Validar estado actual
2. Obtener estado CONFIRMED
3. Cambiar estado de la orden
4. Guardar en base de datos
5. Mensaje de éxito

**Mensajes:**
- ✅ "Orden SO-XXXX confirmada exitosamente."
- ❌ "No se puede confirmar una orden en estado 'Delivered'. Debe estar en estado Draft."

**Estado:** DRAFT → CONFIRMED

---

#### **Acción: ENTREGAR (action=deliver)**

**Validaciones:**
- Estado debe ser CONFIRMED

**Proceso Completo:**

1. **Validar estado:**
   ```python
   if order.status.symbol != 'CONFIRMED':
       # Error y redirigir
   ```

2. **Crear movimientos de inventario:**
   ```python
   created_movements = create_inventory_movements_for_sales_order(
       order, 
       user=request.user
   )
   ```
   - Se crean movimientos tipo `SALE_OUT`
   - Decrementa stock en `source_location`
   - Un movimiento por cada línea de la orden
   - Cantidad negativa (salida de inventario)

3. **Actualizar cantidades entregadas:**
   ```python
   for line in order.lines.all():
       line.delivered_quantity = line.quantity
       line.save()
   ```

4. **Cambiar estado:**
   ```python
   estado_delivered = OrderStatus.objects.get(symbol='DELIVERED')
   order.status = estado_delivered
   order.save()
   ```

5. **Crear asiento contable automático:**
   ```python
   journal_entry = create_entry_for_sale(order, user=request.user)
   ```
   - Genera dos asientos contables:
     
     **Asiento 1: Registro de la Venta**
     ```
     Débito:  Cuentas por Cobrar (Activo)   $XXX.XX
     Crédito: Ingresos por Ventas (Ingreso) $XXX.XX
     ```
     
     **Asiento 2: Costo de la Venta**
     ```
     Débito:  Costo de Ventas (Gasto)       $YYY.YY
     Crédito: Inventario (Activo)           $YYY.YY
     ```
   
   - Descripción: "Venta de productos - SO-XXXX"
   - Fecha: Fecha de entrega

6. **Mensajes al usuario:**
   - ✅ "Orden SO-XXXX marcada como entregada exitosamente. Se crearon X movimiento(s) de inventario."
   - ✅ "Asiento contable JE-XXXX generado automáticamente."
   - ⚠️ "⚠️ ORDEN ENTREGADA pero fallo contable: <error>" (si falla contabilidad)

**Manejo de Errores:**
- `InventoryLocation.DoesNotExist`: Sin ubicaciones configuradas
- `MovementType.DoesNotExist`: Sin tipo SALE_OUT configurado
- `ValidationError`: Error de validación en inventario o contabilidad
- `Exception`: Otros errores

**Estado:** CONFIRMED → DELIVERED

---

#### **Acción: CANCELAR (action=cancel)**

**Validaciones:**
- Estado debe ser DRAFT o CONFIRMED

**Proceso:**
1. Validar estado actual
2. Obtener estado CANCELLED
3. Cambiar estado de la orden
4. Guardar en base de datos
5. No genera movimientos ni asientos
6. Mensaje de éxito

**Mensajes:**
- ✅ "Orden SO-XXXX cancelada exitosamente."
- ❌ "No se puede cancelar una orden en estado 'Delivered'. Solo órdenes en Draft o Confirmed pueden cancelarse."

**Estado:** DRAFT/CONFIRMED → CANCELLED

---

**Contexto del Template:**
```python
{
    'order': <SalesOrder con todas sus relaciones>
}
```

---

### 5. **customer_detail_api**
API que retorna detalles de un cliente en JSON.

**URL:** `/sales/api/customer/<customer_id>/`  
**Método:** GET  
**Parámetro:** `customer_id` puede ser PK numérico o `id_customer` (ej: CUST-001)

**Respuesta Exitosa (200):**
```json
{
    "id": 1,
    "id_customer": "CUST-001",
    "name": "ACME Corporation",
    "legal_name": "ACME Corp S.A.",
    "address": "123 Main Street",
    "city": "Santiago",
    "state_province": "Región Metropolitana",
    "country": "Chile",
    "phone": "+56 2 2345 6789",
    "email": "contact@acme.com",
    "contact_name": "John Doe",
    "status": "Active"
}
```

**Respuestas de Error:**
- **404:** `{"error": "Cliente no encontrado o inactivo"}`
- **405:** `{"error": "Método no permitido"}`
- **500:** `{"error": "<mensaje>"}`

**Validación:**
- Solo retorna clientes con `status=True` (activos)

**Lógica de búsqueda:**
1. Intenta buscar por `id_customer` (código ERP)
2. Si falla, intenta por PK numérico
3. Si ambos fallan, retorna 404

---

### 6. **material_detail_api**
API que retorna detalles de un material en JSON.

**URL:** `/sales/api/material/<material_id>/`  
**Método:** GET  
**Parámetro:** `material_id` puede ser PK numérico o `id_material` (ej: MP-105)

**Respuesta Exitosa (200):**
```json
{
    "id": 1,
    "id_material": "PROD-001",
    "name": "Producto XYZ",
    "description": "Descripción del producto",
    "unit": {
        "id": 1,
        "name": "Unidad",
        "symbol": "unid"
    },
    "status": "Active"
}
```

**Respuestas de Error:**
- **404:** `{"error": "Material no encontrado"}`
- **405:** `{"error": "Método no permitido"}`
- **500:** `{"error": "<mensaje>"}`

**Lógica de búsqueda:**
1. Intenta buscar por `id_material` (código ERP)
2. Si falla, intenta por PK numérico
3. Si ambos fallan, retorna 404

---

### 7. **create_sales_order_api**
API para crear orden de venta con sus líneas (JSON).

**URL:** `/sales/api/create/`  
**Método:** POST  
**Content-Type:** `application/json`  
**Decoradores:** `@csrf_exempt`

**Payload JSON Esperado:**
```json
{
    "customer_id": "CUST-001",
    "source_location_id": 1,
    "notes": "Entrega urgente",
    "lines": [
        {
            "material_id": 1,
            "quantity": 10,
            "unit_id": 1,
            "price": 150.00,
            "currency_id": 1
        },
        {
            "material_id": "PROD-002",
            "quantity": 5,
            "unit_id": 2,
            "price": 200.00,
            "currency_id": 1
        }
    ]
}
```

**Campos Requeridos:**
- `customer_id`: ID o código del cliente (string o int)
- `lines`: Array de líneas (mínimo 1)

**Campos Opcionales:**
- `source_location_id`: ID de ubicación origen (int)
- `notes`: Notas adicionales (string)

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
   - customer_id presente
   - lines no vacío y es array

4. **Validar cliente existe y está activo:**
   ```python
   customer = Customer.objects.get(id_customer=customer_id, status=True)
   # o por pk si falla
   ```

5. **Validar ubicación (si se proporciona):**
   ```python
   source_location = InventoryLocation.objects.get(pk=source_location_id)
   ```

6. **Obtener estado DRAFT:**
   ```python
   draft_status = OrderStatus.objects.get(symbol='DRAFT')
   ```

7. **Generar ID único de orden:**
   ```python
   last_order = SalesOrder.objects.all().order_by('-created_at').first()
   if last_order and last_order.id_sales_order.startswith('SO-'):
       last_number = int(last_order.id_sales_order.split('-')[1])
       new_number = last_number + 1
   else:
       new_number = 1
   
   new_order_id = f"SO-{new_number:04d}"
   ```
   Ejemplo: Si el último es SO-0005, genera SO-0006

8. **Crear SalesOrder:**
   ```python
   sales_order = SalesOrder(
       id_sales_order=new_order_id,
       customer=customer,
       issue_date=date.today(),
       status=draft_status,
       source_location=source_location,
       notes=notes,
       created_by=request.user if authenticated else None
   )
   sales_order.save()
   ```

9. **Validar y crear líneas:**
   - Para cada línea en el array:
   - Validar campos requeridos presentes
   - Validar quantity > 0
   - Validar price ≥ 0
   - Buscar material (intenta por código, luego por PK)
   - Validar unit existe
   - Validar currency existe
   - Generar ID de línea: `SO-XXXX-LYYY`
   - Crear SalesOrderLine

**Respuesta Exitosa (200):**
```json
{
    "success": true,
    "message": "Orden de venta SO-0006 creada exitosamente",
    "id_sales_order": "SO-0006"
}
```

**Respuestas de Error:**

**400 - Campos Faltantes:**
```json
{"error": "El campo customer_id es requerido"}
{"error": "Debe incluir al menos una línea de orden"}
```

**400 - Validación de Líneas:**
```json
{"error": "Línea 1: campo \"material_id\" es requerido"}
{"error": "Línea 2: la cantidad debe ser mayor a cero"}
{"error": "Línea 3: el precio no puede ser negativo"}
{"error": "Línea 1: material con ID 999 no encontrado"}
{"error": "Línea 2: unidad con ID 99 no encontrada"}
```

**400 - Entidad No Encontrada:**
```json
{"error": "Cliente \"CUST-999\" no encontrado o inactivo"}
{"error": "Ubicación con ID 99 no encontrada"}
```

**400 - JSON Inválido:**
```json
{"error": "JSON inválido"}
```

**405 - Método No Permitido:**
```json
{"error": "Método no permitido"}
```

**500 - Error Interno:**
```json
{"error": "Estado DRAFT no encontrado en el sistema"}
{"error": "Error interno: <mensaje>"}
```

**Transaccionalidad:**
- Usa `transaction.atomic()`
- Si falla cualquier validación o creación, hace rollback completo
- Garantiza que no se creen órdenes incompletas

---

## Flujo de Trabajo Completo

### 1. Crear Orden de Venta

**Opción A: Interfaz Web**

1. Acceder a `/sales/sales-order/new/`
2. Completar formulario:
   - Seleccionar cliente
   - Seleccionar ubicación origen (opcional)
   - Ingresar notas (opcional)
3. Agregar líneas de productos:
   - Buscar y seleccionar material
   - Ingresar cantidad
   - Seleccionar unidad
   - Ingresar precio unitario
   - Seleccionar moneda
4. JavaScript envía POST JSON a API
5. Sistema genera SO-XXXX automáticamente
6. Estado inicial: DRAFT
7. Redirige a detalle de orden creada

**Opción B: API Directa**

```python
import requests
import json

url = "http://localhost:8000/sales/api/create/"
headers = {"Content-Type": "application/json"}

data = {
    "customer_id": "CUST-001",
    "source_location_id": 1,
    "notes": "Entrega urgente",
    "lines": [
        {
            "material_id": 1,
            "quantity": 10,
            "unit_id": 1,
            "price": 150.00,
            "currency_id": 1
        }
    ]
}

response = requests.post(url, headers=headers, data=json.dumps(data))
print(response.json())
# {'success': True, 'message': 'Orden de venta SO-0001 creada exitosamente', ...}
```

---

### 2. Confirmar Orden

**Proceso:**
1. Acceder a detalle de orden: `/sales/sales-order/SO-0001/`
2. Verificar que estado es DRAFT
3. Click en botón "Confirmar Orden" (POST action=confirm)
4. Sistema cambia estado a CONFIRMED
5. Orden queda confirmada, lista para entregar

**Estado:** DRAFT → CONFIRMED

---

### 3. Entregar Productos

**Proceso Completo:**

1. Acceder a detalle de orden: `/sales/sales-order/SO-0001/`
2. Verificar que estado es CONFIRMED
3. Click en botón "Entregar Orden" (POST action=deliver)
4. Sistema ejecuta automáticamente:

   **a) Crear movimientos de inventario:**
   ```python
   Movimiento 1:
     - Tipo: SALE_OUT
     - Material: PROD-001
     - Cantidad: -10 (negativa = salida)
     - Ubicación: BOD-01
     - Referencia: SO-0001
   
   Movimiento 2:
     - Tipo: SALE_OUT
     - Material: PROD-002
     - Cantidad: -5
     - Ubicación: BOD-01
     - Referencia: SO-0001
   ```

   **b) Actualizar cantidades entregadas:**
   ```python
   SO-0001-L001: delivered_quantity = 10 (era 0)
   SO-0001-L002: delivered_quantity = 5 (era 0)
   ```

   **c) Cambiar estado:**
   ```python
   Estado: CONFIRMED → DELIVERED
   ```

   **d) Crear asientos contables:**
   ```python
   Asiento 1: JE-XXXX
   Descripción: "Venta de productos - SO-0001"
   Fecha: 2024-11-23
   
   Líneas:
     Débito:  Cuentas por Cobrar (Activo)   $2,000.00
     Crédito: Ingresos por Ventas (Ingreso) $2,000.00
   
   Asiento 2: JE-YYYY
   Descripción: "Costo de venta - SO-0001"
   Fecha: 2024-11-23
   
   Líneas:
     Débito:  Costo de Ventas (Gasto)      $1,200.00
     Crédito: Inventario (Activo)          $1,200.00
   ```

5. Mensajes de confirmación:
   - ✅ "Orden SO-0001 marcada como entregada exitosamente"
   - ✅ "Se crearon 2 movimientos de inventario"
   - ✅ "Asiento contable JE-XXXX generado automáticamente"

**Estado:** CONFIRMED → DELIVERED

---

### 4. Cancelar Orden

**Antes de Entregar:**
1. Acceder a detalle de orden
2. Verificar que estado es DRAFT o CONFIRMED
3. Click en "Cancelar Orden" (POST action=cancel)
4. Estado cambia a CANCELLED
5. No se generan movimientos ni asientos

**Estado:** DRAFT/CONFIRMED → CANCELLED

⚠️ **Nota:** No se pueden cancelar órdenes DELIVERED

---

## Integraciones con Otros Módulos

### **Customers (Clientes)**
- `SalesOrder.customer`: FK a Customer
- Validación: Cliente debe existir y estar activo (status=True)
- Datos del cliente se usan en reportes y documentos

### **Materials (Materiales)**
- `SalesOrderLine.material`: FK a Material
- Validación: Material debe existir
- Unidad y precio por línea

### **Inventory (Inventario)**
- **Función:** `create_inventory_movements_for_sales_order(order, user)`
- **Cuando:** Al entregar orden (DELIVERED)
- **Qué hace:**
  - Crea movimientos tipo SALE_OUT
  - Decrementa stock en source_location
  - Un movimiento por cada línea
  - Cantidad negativa (salida)
- **Referencia:** id_sales_order en movimiento

### **Accounting (Contabilidad)**
- **Función:** `create_entry_for_sale(order, user)`
- **Cuando:** Al entregar orden (DELIVERED)
- **Qué hace:**
  - Crea dos asientos contables automáticos
  - Asiento 1: Registro de venta (Cuentas por Cobrar / Ingresos)
  - Asiento 2: Costo de venta (Costo de Ventas / Inventario)
  - Monto: Total de la orden
- **Descripción:** "Venta de productos - SO-XXXX"

### **Core**
- Usa `Currency` para monedas
- Comparte `OrderStatus` con Purchases

### **Users**
- `created_by`: Usuario que creó la orden
- Control de permisos para acciones

---

## Reglas de Negocio

### 1. **Numeración Automática**
- Sistema genera IDs únicos: SO-0001, SO-0002, etc.
- Formato: `SO-{número:04d}`
- Secuencial e incremental
- Líneas: `{id_sales_order}-L{position:03d}`

### 2. **Estados y Transiciones Permitidas**

**Desde DRAFT:**
- ✅ CONFIRMED (confirmación)
- ✅ CANCELLED (cancelación)

**Desde CONFIRMED:**
- ✅ DELIVERED (entrega)
- ✅ CANCELLED (cancelación)

**Desde DELIVERED:**
- ❌ Estado final, no permite cambios

**Desde CANCELLED:**
- ❌ Estado final, no permite cambios

### 3. **Validaciones de Cantidades**
- `quantity` en línea debe ser > 0
- `price` en línea debe ser ≥ 0
- `delivered_quantity` se inicializa en 0
- Al entregar: `delivered_quantity = quantity`

### 4. **Integridad Referencial**
- `customer`: PROTECT (no se puede eliminar cliente en uso)
- `material`: PROTECT (no se puede eliminar material en uso)
- `status`: PROTECT (no se puede eliminar estado en uso)
- `unit_material`: PROTECT (no se puede eliminar unidad en uso)
- `currency_customer`: PROTECT (no se puede eliminar moneda en uso)
- `sales_order` en líneas: CASCADE (eliminar orden elimina líneas)
- `source_location`: PROTECT (no se puede eliminar ubicación en uso)

### 5. **Ubicación Origen**
- Campo opcional al crear orden
- Requerida para crear movimientos de inventario
- Si no existe, inventario usa ubicación por defecto
- Puede ser null

### 6. **Auditoría**
- Todos los modelos tienen `created_at`, `updated_at`
- Registro de usuario creador (`created_by`)
- Timestamps automáticos

### 7. **Edición Restringida**
- Solo órdenes en DRAFT pueden editarse
- CONFIRMED, DELIVERED, CANCELLED son inmutables
- Usar cancelación en lugar de eliminación

---

## Ejemplos de Código

### Crear Orden Programáticamente:
```python
from sales.models import SalesOrder, SalesOrderLine
from customers.models import Customer
from materials.models import Material, Unit
from core.models import Currency
from purchases.models import OrderStatus
from inventory.models import InventoryLocation
from datetime import date
from decimal import Decimal

# Obtener referencias
cliente = Customer.objects.get(id_customer='CUST-001', status=True)
estado_draft = OrderStatus.objects.get(symbol='DRAFT')
ubicacion = InventoryLocation.objects.get(code='BOD-01')

# Crear orden
orden = SalesOrder.objects.create(
    id_sales_order='SO-0001',
    customer=cliente,
    issue_date=date.today(),
    status=estado_draft,
    source_location=ubicacion,
    notes='Entrega urgente',
    created_by=request.user
)

# Agregar líneas
material1 = Material.objects.get(id_material='PROD-001')
unidad_unid = Unit.objects.get(symbol='unid')
moneda_usd = Currency.objects.get(code='USD')

SalesOrderLine.objects.create(
    id_sales_order_line='SO-0001-L001',
    sales_order=orden,
    material=material1,
    position=1,
    quantity=10,
    unit_material=unidad_unid,
    price=Decimal('150.00'),
    currency_customer=moneda_usd,
    delivered_quantity=0,
    created_by=request.user
)

print(f"Orden creada: {orden}")
totales = orden.get_total_amount()
print(f"Totales: {totales}")  # {'USD': Decimal('1500.00')}
```

---

### Buscar y Filtrar Órdenes:
```python
from sales.models import SalesOrder
from django.db.models import Q

# Todas las órdenes
todas = SalesOrder.objects.all()

# Órdenes en borrador
borradores = SalesOrder.objects.filter(status__symbol='DRAFT')

# Órdenes confirmadas
confirmadas = SalesOrder.objects.filter(status__symbol='CONFIRMED')

# Órdenes entregadas
entregadas = SalesOrder.objects.filter(status__symbol='DELIVERED')

# Órdenes de un cliente
cliente = Customer.objects.get(id_customer='CUST-001')
ordenes_cliente = SalesOrder.objects.filter(customer=cliente)

# Órdenes por rango de fechas
from datetime import date
hoy = date.today()
primer_dia_mes = hoy.replace(day=1)
ordenes_mes = SalesOrder.objects.filter(
    issue_date__gte=primer_dia_mes,
    issue_date__lte=hoy
)

# Buscar por texto (ID o cliente)
busqueda = SalesOrder.objects.filter(
    Q(id_sales_order__icontains='SO-') |
    Q(customer__name__icontains='acme')
)

# Órdenes con ubicación origen específica
ubicacion = InventoryLocation.objects.get(code='BOD-01')
ordenes_ubicacion = SalesOrder.objects.filter(
    source_location=ubicacion
)

# Ordenar por fecha de creación
recientes = SalesOrder.objects.all().order_by('-created_at')[:10]
```

---

### Calcular Totales y Estadísticas:
```python
from sales.models import SalesOrder
from django.db.models import Sum, Count, Avg, F
from decimal import Decimal

# Total por orden
orden = SalesOrder.objects.get(id_sales_order='SO-0001')
totales = orden.get_total_amount()
print(f"Totales por moneda: {totales}")

# Estado de entrega
estado_entrega = orden.get_delivery_status()
print(f"Estado: {estado_entrega}")  # 'not_delivered', 'partially_delivered', 'fully_delivered'

# Órdenes por estado
por_estado = SalesOrder.objects.values('status__name').annotate(
    total=Count('id')
).order_by('-total')

for item in por_estado:
    print(f"{item['status__name']}: {item['total']}")

# Órdenes por cliente
por_cliente = SalesOrder.objects.values('customer__name').annotate(
    total=Count('id')
).order_by('-total')

# Total de líneas en una orden
num_lineas = orden.lines.count()
print(f"Orden {orden.id_sales_order} tiene {num_lineas} líneas")

# Cantidad pendiente de entrega
for linea in orden.lines.all():
    pendiente = linea.get_pending_quantity()
    if pendiente > 0:
        print(f"{linea.material.name}: {pendiente} {linea.unit_material.symbol} pendientes")
```

---

### Confirmar Orden Manualmente:
```python
from sales.models import SalesOrder
from purchases.models import OrderStatus
from django.db import transaction

orden = SalesOrder.objects.get(id_sales_order='SO-0001')

# Verificar estado
if orden.status.symbol != 'DRAFT':
    print(f"❌ No se puede confirmar orden en estado {orden.status.name}")
else:
    with transaction.atomic():
        estado_confirmed = OrderStatus.objects.get(symbol='CONFIRMED')
        orden.status = estado_confirmed
        orden.save()
        print(f"✅ Orden {orden.id_sales_order} confirmada")
```

---

### Entregar Orden Manualmente:
```python
from sales.models import SalesOrder, OrderStatus
from inventory.utils import create_inventory_movements_for_sales_order
from accounting.utils import create_entry_for_sale
from django.db import transaction

orden = SalesOrder.objects.get(id_sales_order='SO-0001')

# Verificar estado
if orden.status.symbol != 'CONFIRMED':
    print(f"❌ No se puede entregar orden en estado {orden.status.name}")
else:
    with transaction.atomic():
        # Crear movimientos de inventario
        movimientos = create_inventory_movements_for_sales_order(
            orden, 
            user=None  # o request.user
        )
        print(f"✅ Creados {len(movimientos)} movimientos de inventario")
        
        # Actualizar cantidades entregadas
        for line in orden.lines.all():
            line.delivered_quantity = line.quantity
            line.save()
        
        # Cambiar estado
        estado_delivered = OrderStatus.objects.get(symbol='DELIVERED')
        orden.status = estado_delivered
        orden.save()
        
        # Crear asientos contables
        try:
            asientos = create_entry_for_sale(orden, user=None)
            if asientos:
                print(f"✅ Asientos contables creados")
        except Exception as e:
            print(f"⚠️ Error en contabilidad: {str(e)}")
        
        print(f"✅ Orden {orden.id_sales_order} entregada exitosamente")
```

---

### Cancelar Orden:
```python
orden = SalesOrder.objects.get(id_sales_order='SO-0002')

# Verificar estado
if orden.status.symbol not in ['DRAFT', 'CONFIRMED']:
    print(f"❌ No se puede cancelar orden en estado {orden.status.name}")
else:
    estado_cancelled = OrderStatus.objects.get(symbol='CANCELLED')
    orden.status = estado_cancelled
    orden.save()
    print(f"✅ Orden {orden.id_sales_order} cancelada")
```

---

### Exportar Órdenes a CSV:
```python
import csv
from django.http import HttpResponse
from sales.models import SalesOrder

def export_sales_orders_csv(queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sales_orders.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'ID Orden', 'Cliente', 'Fecha Emisión', 'Estado', 
        'Total USD', 'Creado Por'
    ])
    
    for orden in queryset:
        totales = orden.get_total_amount()
        total_usd = totales.get('USD', 0)
        
        writer.writerow([
            orden.id_sales_order,
            orden.customer.name,
            orden.issue_date.strftime('%Y-%m-%d'),
            orden.status.name,
            f'{total_usd:.2f}',
            orden.created_by.username if orden.created_by else ''
        ])
    
    return response

# Uso
ordenes_mes = SalesOrder.objects.filter(
    issue_date__month=11,
    issue_date__year=2024
)
response = export_sales_orders_csv(ordenes_mes)
```

---

## Notas Importantes

### ⚠️ **Advertencias:**

1. **No Eliminar Órdenes Entregadas:**
   - Pérdida de historial de inventario
   - Inconsistencia en contabilidad
   - Usar CANCELLED en su lugar

2. **Validar Estado Antes de Acciones:**
   - Cada acción tiene estados válidos
   - Sistema valida pero frontend debe prevenir

3. **Ubicación Origen:**
   - Requerida para movimientos de inventario
   - Validar que existe y está activa
   - Configurar ubicaciones antes de entregar

4. **Tipos de Movimiento:**
   - Ejecutar `init_movement_types` antes de usar
   - SALE_OUT debe existir
   - Sin él, entrega falla

5. **Configuración Contable:**
   - Cuentas de Inventario, Cuentas por Cobrar, Ingresos, Costo de Ventas deben existir
   - País y moneda configurados
   - Si falla, orden se entrega pero sin asientos

6. **Stock Disponible:**
   - Validar stock antes de entregar
   - Sistema no previene ventas sin stock
   - Puede generar inventario negativo

---

### 💡 **Tips:**

1. **IDs Descriptivos:**
   - Usar prefijos claros: SO-XXXX
   - Mantener formato consistente
   - Facilita búsqueda y organización

2. **Validación Frontend:**
   - Validar antes de enviar a API
   - Mostrar errores claros
   - Prevenir envíos inválidos

3. **Optimización de Queries:**
   - Usar `select_related()` para FKs
   - Usar `prefetch_related()` para líneas
   - Reducir consultas N+1

4. **Mensajes Claros:**
   - Informar al usuario cada acción
   - Distinguir success, warning, error
   - Incluir detalles relevantes

5. **Logging:**
   - Registrar operaciones importantes
   - Facilita debugging
   - Auditoría de acciones

6. **Precios Actualizados:**
   - Obtener precios de catálogo de materiales
   - Permitir ajustes manuales
   - Documentar descuentos

---

### 📊 **Mejores Prácticas:**

1. **Flujo Completo:**
   - DRAFT: Crear y editar
   - CONFIRMED: Confirmar antes de entregar
   - DELIVERED: Entregar productos
   - No usar CANCELLED innecesariamente

2. **Control de Cambios:**
   - No editar órdenes DELIVERED
   - Cancelar en lugar de eliminar
   - Mantener historial intacto

3. **Revisión Antes de Entregar:**
   - Validar cantidades
   - Verificar precios
   - Confirmar cliente y productos

4. **Integración Automática:**
   - Aprovechar movimientos automáticos
   - Confiar en asientos contables automáticos
   - Validar pero no duplicar manualmente

5. **Reportes y Análisis:**
   - Exportar datos regularmente
   - Analizar por cliente
   - Comparar precios de venta
   - Identificar productos más vendidos

---

### 🔧 **Mantenimiento:**

1. **Órdenes Antiguas:**
   ```python
   # Revisar órdenes en DRAFT hace más de 30 días
   from datetime import timedelta
   from django.utils import timezone
   
   hace_30_dias = timezone.now() - timedelta(days=30)
   
   ordenes_antiguas = SalesOrder.objects.filter(
       status__symbol='DRAFT',
       created_at__lt=hace_30_dias
   )
   
   print(f"Órdenes DRAFT antiguas: {ordenes_antiguas.count()}")
   ```

2. **Auditoría de Estados:**
   ```python
   # Verificar órdenes sin líneas
   sin_lineas = SalesOrder.objects.annotate(
       num_lines=Count('lines')
   ).filter(num_lines=0)
   
   print(f"Órdenes sin líneas: {sin_lineas.count()}")
   ```

3. **Validación de Integridad:**
   ```python
   # Órdenes DELIVERED sin movimientos de inventario
   from inventory.models import InventoryMovement
   
   entregadas = SalesOrder.objects.filter(status__symbol='DELIVERED')
   
   for orden in entregadas:
       movimientos = InventoryMovement.objects.filter(
           reference_document=orden.id_sales_order
       )
       if not movimientos.exists():
           print(f"⚠️ Orden {orden.id_sales_order} sin movimientos")
   ```

4. **Limpieza de Datos:**
   ```python
   # Eliminar órdenes DRAFT vacías muy antiguas
   hace_90_dias = timezone.now() - timedelta(days=90)
   
   a_eliminar = SalesOrder.objects.annotate(
       num_lines=Count('lines')
   ).filter(
       num_lines=0,
       status__symbol='DRAFT',
       created_at__lt=hace_90_dias
   )
   
   print(f"A eliminar: {a_eliminar.count()}")
   # a_eliminar.delete()  # Con precaución
   ```

---

## Resumen Técnico

**Modelos:** 2 (SalesOrder, SalesOrderLine) + OrderStatus compartido  
**Vistas:** 7 (list, create, edit, detail, 3 APIs)  
**URLs:** 7  
**Métodos de Creación:** Web form + JSON API  
**Paginación:** 10 registros por página  
**Filtros:** 5 (búsqueda, cliente, estado, fecha desde, fecha hasta)  
**Exportación:** CSV  
**Estados:** 4 (DRAFT, CONFIRMED, DELIVERED, CANCELLED)  
**Integraciones:** 4 (Customers, Materials, Inventory, Accounting)  
**Transaccionalidad:** Sí (en API y acciones de entrega)  

**Dependencias:**
- customers.Customer
- materials.Material, Unit
- core.Currency
- purchases.OrderStatus (compartido)
- inventory.InventoryLocation, utils
- accounting.utils
- users.User

**Funciones de Utilidad Externas:**
- `create_inventory_movements_for_sales_order(order, user)` (inventory.utils)
- `create_entry_for_sale(order, user)` (accounting.utils)
