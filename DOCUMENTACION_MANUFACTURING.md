# 🏭 Módulo de Manufactura (Manufacturing)

## Descripción General
Módulo encargado de la gestión de procesos de manufactura/producción, incluyendo Bill of Materials (BOM), órdenes de trabajo, consumo de materias primas y generación de productos terminados, con integración automática a inventario y contabilidad.

---

## Modelos Principales

### 1. **WorkOrderStatus** (Estado de Orden de Trabajo)
Catálogo de estados para las órdenes de producción.

**Campos:**
- `name`: Nombre del estado - CharField(100)
- `symbol`: Símbolo único - CharField(20, unique=True)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, SET_NULL, null=True)

**Métodos:**
- `__str__()`: Retorna formato "Name (Symbol)"
  ```python
  def __str__(self):
      return f"{self.name} ({self.symbol})"
  ```

**Tabla de Base de Datos:** `work_order_status`

**Estados del Sistema:**
```
- DRAFT (Borrador): Orden creada pero no iniciada
- IN_PROGRESS (En Proceso): Producción en curso
- DONE (Terminado): Producción completada
- CANCELLED (Cancelada): Orden anulada
```

**Índices:**
- `symbol` (unique, búsqueda rápida)
- `name` (ordenamiento alfabético)

---

### 2. **BillOfMaterials (BOM)** (Lista de Materiales)
Define la receta de producción: qué materiales se necesitan para fabricar un producto.

**Campos:**
- `id_bill_of_materials`: Código único (ej: BOM-001) - CharField(50, unique=True)
- `material`: Producto terminado que se fabrica - ForeignKey(Material, PROTECT)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, SET_NULL, null=True)

**Métodos:**
- `__str__()`: Retorna formato "BOM ID - Material Name"
  ```python
  def __str__(self):
      return f"BOM {self.id_bill_of_materials} - {self.material.name}"
  ```

**Tabla de Base de Datos:** `bill_of_materials`

**Related Names:**
- `lines`: Líneas del BOM (componentes requeridos)
- `work_orders` (desde WorkOrder): Órdenes que usan este BOM

**Ejemplo Conceptual:**
```
BOM-001: Silla de Oficina
├─ Asiento de tela x1
├─ Respaldo x1
├─ Base giratoria x1
├─ Ruedas x5
└─ Tornillos x20
```

---

### 3. **BillOfMaterialsLine** (Línea de BOM)
Detalla cada componente/material requerido en el BOM.

**Campos:**
- `bill_of_materials`: BOM padre - ForeignKey(BillOfMaterials, CASCADE)
- `component`: Material/componente necesario - ForeignKey(Material, PROTECT)
- `quantity`: Cantidad del componente - IntegerField
- `unit_component`: Unidad de medida - ForeignKey(Unit, PROTECT)

**Métodos:**
- `__str__()`: Retorna formato "Component Name xQuantity"
  ```python
  def __str__(self):
      return f"{self.component.name} x{self.quantity}"
  ```

**Tabla de Base de Datos:** `lines_bill_of_materials`

**Índices:**
- Ordenamiento por BOM y componente

**Constraint:**
- Cada línea pertenece a un solo BOM
- Si se elimina BOM, se eliminan sus líneas (CASCADE)

**Ejemplo:**
```python
BOM: Silla de Oficina
Línea 1: Asiento de tela x1 unid
Línea 2: Respaldo x1 unid
Línea 3: Base giratoria x1 unid
Línea 4: Ruedas x5 unid
Línea 5: Tornillos x20 unid
```

---

### 4. **WorkOrder** (Orden de Trabajo/Producción)
Representa una orden de producción que consume materias primas y genera productos terminados.

**Campos:**
- `id_work_order`: Código único (ej: WO-0001) - CharField(50, unique=True)
- `bill_of_materials`: BOM a producir - ForeignKey(BillOfMaterials, PROTECT)
- `quantity`: Cantidad a producir - IntegerField
- `status`: Estado de la orden - ForeignKey(WorkOrderStatus, PROTECT)
- `origin_location`: Ubicación de consumo de MP - ForeignKey(InventoryLocation, PROTECT, null=True)
- `destination_location`: Ubicación de entrada de PT - ForeignKey(InventoryLocation, PROTECT, null=True)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, SET_NULL, null=True)

**Métodos:**
- `__str__()`: Retorna formato "ID - Material Name"
  ```python
  def __str__(self):
      return f"{self.id_work_order} - {self.bill_of_materials.material.name}"
  ```

**Tabla de Base de Datos:** `work_order`

**Índices:**
- `id_work_order` (unique, búsqueda rápida)
- `-created_at` (órdenes más recientes primero)

**Related Names:**
- `work_orders_origin` (desde InventoryLocation): Órdenes que consumen de esta ubicación
- `work_orders_destination` (desde InventoryLocation): Órdenes que producen en esta ubicación

---

## URLs Disponibles

```python
# Vista principal (tablero Kanban)
/manufacturing/work-order/                  # Lista de órdenes (Kanban board)

# CRUD
/manufacturing/work-order/new/              # Crear nueva orden de producción

# Detalle
/manufacturing/work-order/<wo_id>/          # Ver detalle de orden
```

---

## Vistas (Views)

### 1. **work_order_list_view**
Vista principal tipo tablero Kanban con órdenes separadas por estado.

**URL:** `/manufacturing/work-order/`  
**Métodos:** GET, POST  
**Decorador:** `@login_required`

**Vista GET - Tablero Kanban:**

Muestra órdenes de producción organizadas en columnas por estado:
- **Borrador (DRAFT):** Órdenes creadas pero no iniciadas
- **En Proceso (IN_PROGRESS):** Producción activa
- **Terminado (DONE):** Producción completada
- **Cancelada (CANCELLED):** Órdenes anuladas

**Contexto del Template:**
```python
{
    'draft_orders': <WorkOrder con status=DRAFT>,
    'in_progress_orders': <WorkOrder con status=IN_PROGRESS>,
    'done_orders': <WorkOrder con status=DONE>,
    'cancelled_orders': <WorkOrder con status=CANCELLED>
}
```

---

**Acciones POST:**

### **Acción: INICIAR (action=start)**

Inicia una orden de producción (DRAFT → IN_PROGRESS).

**Parámetros POST:**
- `action`: "start"
- `work_order_id`: ID de la orden (ej: WO-0001)

**Validaciones:**
- Estado actual debe ser DRAFT
- Orden debe existir

**Proceso:**
1. Validar estado actual es DRAFT
2. Obtener o crear estado IN_PROGRESS
3. Cambiar estado de la orden
4. Guardar en base de datos
5. Mensaje de éxito

**Mensajes:**
- ✅ "Orden WO-XXXX iniciada."
- ❌ "La orden no está en estado Borrador."

**Estado:** DRAFT → IN_PROGRESS

---

### **Acción: TERMINAR (action=finish)**

Completa la producción, consume materias primas y genera producto terminado.

**Parámetros POST:**
- `action`: "finish"
- `work_order_id`: ID de la orden

**Validaciones:**
- Estado debe ser IN_PROGRESS
- Ubicaciones origen/destino configuradas
- Stock suficiente de todos los componentes

**Proceso Completo:**

1. **Validar estado:**
   ```python
   if work_order.status.symbol != 'IN_PROGRESS':
       # Error
   ```

2. **Validar ubicaciones:**
   ```python
   if not work_order.origin_location or not work_order.destination_location:
       # Asignar ubicación por defecto
       default_location = get_default_inventory_location()
       work_order.origin_location = default_location
       work_order.destination_location = default_location
       work_order.save()
   ```

3. **Validar stock de componentes:**
   ```python
   for line in work_order.bill_of_materials.lines.all():
       # Calcular stock disponible en ubicación origen
       total_in = InventoryMovement.objects.filter(
           material=line.component,
           location=work_order.origin_location,
           movement_type__symbol__endswith='_IN'
       ).aggregate(total=Sum('quantity'))['total'] or 0
       
       total_out = InventoryMovement.objects.filter(
           material=line.component,
           location=work_order.origin_location,
           movement_type__symbol__endswith='_OUT'
       ).aggregate(total=Sum('quantity'))['total'] or 0
       
       available = total_in - total_out
       required = line.quantity * work_order.quantity
       
       if required > available:
           # Stock insuficiente
           insufficient = f"{line.component.name}: requiere {required}, disponible {available}"
           break
   ```

4. **Crear movimientos de inventario:**
   ```python
   created_movements = create_inventory_movements_for_production_order(
       production_order=work_order,
       user=request.user
   )
   ```
   
   **Movimientos Creados:**
   
   **A. Consumo de Materias Primas (salida):**
   ```
   Para cada componente en BOM:
     Movimiento:
       - Tipo: PRODUCTION_OUT
       - Material: componente
       - Cantidad: -quantity_in_bom × quantity_to_produce (negativa)
       - Ubicación: origin_location
       - Referencia: WO-XXXX
   ```
   
   **B. Entrada de Producto Terminado:**
   ```
   Movimiento:
     - Tipo: PRODUCTION_IN
     - Material: producto terminado (BOM.material)
     - Cantidad: +quantity_to_produce (positiva)
     - Ubicación: destination_location
     - Referencia: WO-XXXX
   ```

5. **Cambiar estado:**
   ```python
   done_status = WorkOrderStatus.objects.get_or_create(
       symbol='DONE',
       defaults={'name': 'Terminado'}
   )
   work_order.status = done_status
   work_order.save()
   ```

6. **Crear asiento contable automático:**
   ```python
   journal_entry = create_entry_for_production(
       work_order,
       user=request.user
   )
   ```
   
   **Asientos Generados:**
   ```
   Asiento: JE-XXXX
   Descripción: "Producción de productos - WO-XXXX"
   Fecha: Fecha de terminación
   
   Líneas:
     Débito:  Inventario Productos Terminados (Activo)  $XXX.XX
     Crédito: Inventario Materias Primas (Activo)       $XXX.XX
   ```

7. **Mensajes al usuario:**
   - ✅ "Orden WO-XXXX terminada. Se crearon X movimientos de inventario."
   - ✅ "Asiento contable JE-XXXX generado automáticamente."
   - ⚠️ "⚠️ ORDEN TERMINADA pero fallo contable: <error>" (si falla contabilidad)

**Manejo de Errores:**
- `WorkOrderStatus.DoesNotExist`: Sin estado IN_PROGRESS configurado
- `ValueError`: Error de configuración (ubicaciones, tipos de movimiento)
- `ValidationError`: Error de validación en contabilidad
- Stock insuficiente: Detalle de material, cantidad requerida vs disponible
- Sin ubicación por defecto: No hay ubicaciones configuradas

**Mensajes de Error:**
- ❌ "Solo se puede terminar una orden en proceso activo."
- ❌ "No hay ubicación de inventario por defecto: <error>"
- ❌ "Stock insuficiente para terminar producción (<detalle>)."
- ❌ "Error de configuración: <mensaje>"
- ❌ "Error al crear movimientos de inventario: <mensaje>"

**Estado:** IN_PROGRESS → DONE

---

### **Acción: CANCELAR (action=cancel)**

Cancela una orden y elimina sus movimientos de inventario asociados.

**Parámetros POST:**
- `action`: "cancel"
- `work_order_id`: ID de la orden

**Proceso:**
1. Buscar movimientos de inventario asociados:
   ```python
   production_movements = InventoryMovement.objects.filter(
       reference=work_order.id_work_order
   )
   ```

2. Eliminar movimientos (si existen):
   ```python
   movements_count = production_movements.count()
   if movements_count > 0:
       production_movements.delete()
   ```

3. Cambiar estado a CANCELLED:
   ```python
   cancelled_status = WorkOrderStatus.objects.get_or_create(
       symbol='CANCELLED',
       defaults={'name': 'Cancelada'}
   )
   work_order.status = cancelled_status
   work_order.save()
   ```

4. Mensajes:
   - ℹ️ "Se eliminaron X movimientos de inventario asociados."
   - ✅ "Orden WO-XXXX cancelada exitosamente."

**Transaccionalidad:**
- Usa `transaction.atomic()`
- Si falla, hace rollback completo
- Garantiza consistencia

**Estado:** CUALQUIER → CANCELLED

---

### 2. **work_order_form_view**
Formulario para crear nueva orden de producción.

**URL:** `/manufacturing/work-order/new/`  
**Métodos:** GET, POST  
**Decorador:** `@login_required`

**Flujo GET:**
1. Obtiene todos los BOMs disponibles
2. Obtiene ubicaciones activas
3. Renderiza formulario

**Contexto GET:**
```python
{
    'bom_list': <BillOfMaterials ordenados por material>,
    'locations': <InventoryLocation activas ordenadas por nombre>
}
```

**Flujo POST:**

**Parámetros POST:**
- `bill_of_materials`: ID del BOM (int)
- `quantity`: Cantidad a producir (int)
- `origin_location`: ID de ubicación origen (int, opcional)
- `destination_location`: ID de ubicación destino (int, opcional)

**Proceso:**

1. **Validar BOM existe:**
   ```python
   try:
       bom = BillOfMaterials.objects.get(id=bom_id)
   except BillOfMaterials.DoesNotExist:
       # Error
   ```

2. **Validar ubicaciones (si se proporcionan):**
   ```python
   if origin_location_id:
       origin_location = InventoryLocation.objects.get(id=origin_location_id)
   
   if destination_location_id:
       destination_location = InventoryLocation.objects.get(id=destination_location_id)
   ```

3. **Obtener o crear estado DRAFT:**
   ```python
   draft_status = WorkOrderStatus.objects.get_or_create(
       symbol='DRAFT',
       defaults={'name': 'Borrador'}
   )
   ```

4. **Generar ID único:**
   ```python
   count = WorkOrder.objects.count() + 1
   new_id = f"WO-{count:04d}"
   ```
   Ejemplo: Si hay 5 órdenes, genera WO-0006

5. **Crear orden:**
   ```python
   WorkOrder.objects.create(
       id_work_order=new_id,
       bill_of_materials=bom,
       quantity=qty,
       status=draft_status,
       origin_location=origin_location,
       destination_location=destination_location,
       created_by=request.user
   )
   ```

6. **Redirigir:**
   - Mensaje: ✅ "Orden de Producción WO-XXXX creada en estado Borrador."
   - Redirige a: `manufacturing:work_order_list`

**Validaciones:**
- BOM debe existir
- Cantidad debe ser > 0 (validación implícita)
- Ubicaciones deben existir (si se proporcionan)

**Mensajes de Error:**
- ❌ "Debe seleccionar un Bill of Materials válido."
- ❌ "Ubicación de origen no válida."
- ❌ "Ubicación de destino no válida."

---

### 3. **work_order_detail_view**
Vista de detalle de una orden de producción (placeholder).

**URL:** `/manufacturing/work-order/<wo_id>/`  
**Método:** GET  
**Parámetro:** `wo_id` es el código único (ej: WO-0001)  
**Decorador:** `@login_required`

**Proceso:**
1. Busca orden por id_work_order (404 si no existe)
2. Renderiza template con detalle

**Contexto:**
```python
{
    'work_order': <WorkOrder con todas sus relaciones>
}
```

**Nota:** Vista básica, puede extenderse para mostrar:
- Detalle del BOM y componentes
- Movimientos de inventario asociados
- Historial de cambios de estado
- Costos de producción

---

## Flujo de Trabajo Completo

### 1. Crear Bill of Materials (BOM)

**Proceso Programático (no hay vista web aún):**

```python
from manufacturing.models import BillOfMaterials, BillOfMaterialsLine
from materials.models import Material, Unit

# Crear BOM para Silla de Oficina
producto = Material.objects.get(id_material='PROD-SILLA-001')

bom = BillOfMaterials.objects.create(
    id_bill_of_materials='BOM-001',
    material=producto,
    created_by=request.user
)

# Agregar componentes
asiento = Material.objects.get(id_material='MP-ASIENTO')
respaldo = Material.objects.get(id_material='MP-RESPALDO')
base = Material.objects.get(id_material='MP-BASE')
ruedas = Material.objects.get(id_material='MP-RUEDAS')
tornillos = Material.objects.get(id_material='MP-TORNILLOS')

unidad = Unit.objects.get(symbol='unid')

BillOfMaterialsLine.objects.create(
    bill_of_materials=bom,
    component=asiento,
    quantity=1,
    unit_component=unidad
)

BillOfMaterialsLine.objects.create(
    bill_of_materials=bom,
    component=respaldo,
    quantity=1,
    unit_component=unidad
)

BillOfMaterialsLine.objects.create(
    bill_of_materials=bom,
    component=base,
    quantity=1,
    unit_component=unidad
)

BillOfMaterialsLine.objects.create(
    bill_of_materials=bom,
    component=ruedas,
    quantity=5,
    unit_component=unidad
)

BillOfMaterialsLine.objects.create(
    bill_of_materials=bom,
    component=tornillos,
    quantity=20,
    unit_component=unidad
)

print(f"BOM creado: {bom}")
print(f"Componentes: {bom.lines.count()}")
```

---

### 2. Crear Orden de Producción

**Proceso Web:**
1. Ir a `/manufacturing/work-order/new/`
2. Seleccionar BOM (ej: BOM-001 - Silla de Oficina)
3. Ingresar cantidad a producir (ej: 10)
4. Seleccionar ubicación origen (de donde sacar MP)
5. Seleccionar ubicación destino (donde poner PT)
6. Click en "Crear Orden"
7. Sistema genera WO-XXXX automáticamente
8. Estado inicial: DRAFT (Borrador)
9. Redirige a tablero Kanban

**Ejemplo:**
```
BOM: BOM-001 - Silla de Oficina
Cantidad: 10 unidades
Ubicación Origen: BOD-MP (Bodega Materias Primas)
Ubicación Destino: BOD-PT (Bodega Productos Terminados)

Genera: WO-0001
Estado: DRAFT
```

---

### 3. Iniciar Producción

**Proceso:**
1. En tablero Kanban, columna DRAFT
2. Encontrar orden WO-0001
3. Click en "Iniciar Producción" (POST action=start)
4. Sistema cambia estado a IN_PROGRESS
5. Orden se mueve a columna "En Proceso"

**Estado:** DRAFT → IN_PROGRESS

---

### 4. Terminar Producción

**Proceso Completo:**

1. En tablero Kanban, columna IN_PROGRESS
2. Encontrar orden WO-0001
3. Click en "Terminar Producción" (POST action=finish)

4. **Sistema valida stock:**
   ```
   BOM: Silla de Oficina
   Cantidad a producir: 10
   
   Componentes requeridos:
   - Asiento: 10 × 1 = 10 unidades
   - Respaldo: 10 × 1 = 10 unidades
   - Base: 10 × 1 = 10 unidades
   - Ruedas: 10 × 5 = 50 unidades
   - Tornillos: 10 × 20 = 200 unidades
   
   Stock disponible en BOD-MP:
   ✓ Asiento: 15 disponibles (OK)
   ✓ Respaldo: 12 disponibles (OK)
   ✓ Base: 20 disponibles (OK)
   ✓ Ruedas: 100 disponibles (OK)
   ✓ Tornillos: 500 disponibles (OK)
   ```

5. **Crear movimientos de inventario:**
   
   **A. Consumo de MP (salida de BOD-MP):**
   ```
   Movimiento 1:
     Tipo: PRODUCTION_OUT
     Material: Asiento
     Cantidad: -10
     Ubicación: BOD-MP
     Referencia: WO-0001
   
   Movimiento 2:
     Tipo: PRODUCTION_OUT
     Material: Respaldo
     Cantidad: -10
     Ubicación: BOD-MP
     Referencia: WO-0001
   
   Movimiento 3:
     Tipo: PRODUCTION_OUT
     Material: Base
     Cantidad: -10
     Ubicación: BOD-MP
     Referencia: WO-0001
   
   Movimiento 4:
     Tipo: PRODUCTION_OUT
     Material: Ruedas
     Cantidad: -50
     Ubicación: BOD-MP
     Referencia: WO-0001
   
   Movimiento 5:
     Tipo: PRODUCTION_OUT
     Material: Tornillos
     Cantidad: -200
     Ubicación: BOD-MP
     Referencia: WO-0001
   ```
   
   **B. Entrada de PT (entrada a BOD-PT):**
   ```
   Movimiento 6:
     Tipo: PRODUCTION_IN
     Material: Silla de Oficina
     Cantidad: +10
     Ubicación: BOD-PT
     Referencia: WO-0001
   ```

6. **Cambiar estado a DONE**

7. **Crear asiento contable:**
   ```
   Asiento: JE-0015
   Descripción: "Producción de productos - WO-0001"
   Fecha: 2025-11-23
   
   Débito:  Inventario PT   $1,500.00
   Crédito: Inventario MP   $1,500.00
   ```

8. **Mensajes al usuario:**
   - ✅ "Orden WO-0001 terminada. Se crearon 6 movimientos de inventario."
   - ✅ "Asiento contable JE-0015 generado automáticamente."

9. **Orden se mueve a columna "Terminado"**

**Estado:** IN_PROGRESS → DONE

---

### 5. Cancelar Orden

**Escenario A: Cancelar sin movimientos (DRAFT o IN_PROGRESS sin terminar)**
1. Click en "Cancelar"
2. Sistema busca movimientos asociados: 0 encontrados
3. Cambia estado a CANCELLED
4. ✅ "Orden WO-0002 cancelada exitosamente."

**Escenario B: Cancelar con movimientos (DONE)**
1. Click en "Cancelar"
2. Sistema busca movimientos asociados: 6 encontrados
3. Elimina los 6 movimientos (revierte inventario)
4. Cambia estado a CANCELLED
5. ℹ️ "Se eliminaron 6 movimientos de inventario asociados."
6. ✅ "Orden WO-0002 cancelada exitosamente."

⚠️ **Nota:** Cancelar orden DONE revierte el inventario, pero NO revierte asientos contables automáticamente.

**Estado:** CUALQUIER → CANCELLED

---

## Integraciones con Otros Módulos

### **Materials (Materiales)**
- `BillOfMaterials.material`: FK al producto terminado
- `BillOfMaterialsLine.component`: FK a materias primas/componentes
- `BillOfMaterialsLine.unit_component`: FK a unidades de medida

### **Inventory (Inventario)**
- `WorkOrder.origin_location`: Ubicación de consumo de MP
- `WorkOrder.destination_location`: Ubicación de entrada de PT
- **Función:** `create_inventory_movements_for_production_order(production_order, user)`
  - Crea movimientos PRODUCTION_OUT (consumo MP)
  - Crea movimiento PRODUCTION_IN (entrada PT)
  - Referencia: id_work_order

### **Accounting (Contabilidad)**
- **Función:** `create_entry_for_production(work_order, user)`
- Genera asiento al terminar producción
- Débito: Inventario PT
- Crédito: Inventario MP

### **Users (Usuarios)**
- `created_by`: Usuario creador de BOM/Orden
- Control de permisos (login_required)

---

## Reglas de Negocio

### 1. **Numeración Automática**
- Sistema genera IDs únicos: WO-0001, WO-0002, etc.
- Formato: `WO-{número:04d}`
- Secuencial basado en conteo actual
- BOMs deben crearse manualmente con ID único

### 2. **Estados y Transiciones**

**Desde DRAFT:**
- ✅ IN_PROGRESS (iniciar)
- ✅ CANCELLED (cancelar)

**Desde IN_PROGRESS:**
- ✅ DONE (terminar)
- ✅ CANCELLED (cancelar)

**Desde DONE:**
- ✅ CANCELLED (cancelar, revierte inventario)

**Desde CANCELLED:**
- ❌ Estado final

### 3. **Validaciones de Stock**
- Al terminar producción, valida stock de TODOS los componentes
- Calcula: `required = quantity_in_bom × quantity_to_produce`
- Stock disponible = movimientos IN - movimientos OUT
- Si cualquier componente insuficiente → Error, no permite terminar

### 4. **Ubicaciones de Inventario**
- origin_location y destination_location son opcionales
- Si no se especifican al terminar, usa ubicación por defecto
- Si no hay ubicación por defecto → Error

### 5. **Tipos de Movimiento Requeridos**
- `PRODUCTION_OUT`: Para consumo de MP
- `PRODUCTION_IN`: Para entrada de PT
- Deben existir antes de terminar producción
- Si faltan → Error de configuración

### 6. **Integridad Referencial**
- `bill_of_materials`: PROTECT (no eliminar BOM en uso)
- `material` en BOM: PROTECT (no eliminar producto con BOM)
- `component` en línea: PROTECT (no eliminar MP en BOM)
- `status`: PROTECT (no eliminar estado en uso)
- `origin_location/destination_location`: PROTECT
- `bill_of_materials` en líneas: CASCADE (eliminar BOM elimina líneas)

### 7. **Cálculo de Cantidades**
```python
# Para cada componente:
cantidad_requerida = cantidad_en_bom × cantidad_a_producir

# Ejemplo:
# BOM: Silla requiere 5 ruedas
# Producir: 10 sillas
# Cantidad requerida = 5 × 10 = 50 ruedas
```

### 8. **Transaccionalidad**
- Cancelación usa `transaction.atomic()`
- Garantiza que no queden movimientos huérfanos
- Si falla algo, hace rollback completo

---

## Ejemplos de Código

### Crear BOM Completo:
```python
from manufacturing.models import BillOfMaterials, BillOfMaterialsLine
from materials.models import Material, Unit

# Producto terminado
mesa = Material.objects.get(id_material='PROD-MESA-001')

# Crear BOM
bom = BillOfMaterials.objects.create(
    id_bill_of_materials='BOM-MESA-001',
    material=mesa,
    created_by=request.user
)

# Componentes
tablero = Material.objects.get(id_material='MP-TABLERO')
patas = Material.objects.get(id_material='MP-PATA')
tornillos = Material.objects.get(id_material='MP-TORNILLO-M6')
unidad = Unit.objects.get(symbol='unid')

# Agregar líneas
BillOfMaterialsLine.objects.create(
    bill_of_materials=bom,
    component=tablero,
    quantity=1,
    unit_component=unidad
)

BillOfMaterialsLine.objects.create(
    bill_of_materials=bom,
    component=patas,
    quantity=4,
    unit_component=unidad
)

BillOfMaterialsLine.objects.create(
    bill_of_materials=bom,
    component=tornillos,
    quantity=16,
    unit_component=unidad
)

print(f"BOM creado: {bom}")
for line in bom.lines.all():
    print(f"  - {line}")
# Output:
# BOM creado: BOM BOM-MESA-001 - Mesa de Oficina
#   - Tablero x1
#   - Pata x4
#   - Tornillo M6 x16
```

---

### Crear Orden de Producción Programáticamente:
```python
from manufacturing.models import WorkOrder, WorkOrderStatus, BillOfMaterials
from inventory.models import InventoryLocation

# Obtener BOM
bom = BillOfMaterials.objects.get(id_bill_of_materials='BOM-MESA-001')

# Obtener ubicaciones
bod_mp = InventoryLocation.objects.get(code='BOD-MP')
bod_pt = InventoryLocation.objects.get(code='BOD-PT')

# Estado inicial
draft_status = WorkOrderStatus.objects.get(symbol='DRAFT')

# Generar ID
count = WorkOrder.objects.count() + 1
new_id = f"WO-{count:04d}"

# Crear orden
orden = WorkOrder.objects.create(
    id_work_order=new_id,
    bill_of_materials=bom,
    quantity=20,  # Producir 20 mesas
    status=draft_status,
    origin_location=bod_mp,
    destination_location=bod_pt,
    created_by=request.user
)

print(f"Orden creada: {orden}")
# Output: WO-0001 - Mesa de Oficina
```

---

### Consultar Componentes de un BOM:
```python
bom = BillOfMaterials.objects.get(id_bill_of_materials='BOM-MESA-001')

print(f"BOM: {bom}")
print(f"Producto: {bom.material.name}")
print(f"Componentes requeridos:")

for line in bom.lines.all():
    print(f"  - {line.component.name}: {line.quantity} {line.unit_component.symbol}")

# Output:
# BOM: BOM BOM-MESA-001 - Mesa de Oficina
# Producto: Mesa de Oficina
# Componentes requeridos:
#   - Tablero: 1 unid
#   - Pata: 4 unid
#   - Tornillo M6: 16 unid
```

---

### Calcular Materiales Requeridos:
```python
bom = BillOfMaterials.objects.get(id_bill_of_materials='BOM-MESA-001')
cantidad_a_producir = 20

print(f"Para producir {cantidad_a_producir} {bom.material.name}:")

for line in bom.lines.all():
    requerido = line.quantity * cantidad_a_producir
    print(f"  - {line.component.name}: {requerido} {line.unit_component.symbol}")

# Output:
# Para producir 20 Mesa de Oficina:
#   - Tablero: 20 unid
#   - Pata: 80 unid
#   - Tornillo M6: 320 unid
```

---

### Validar Stock Antes de Producir:
```python
from django.db.models import Sum
from inventory.models import InventoryMovement

orden = WorkOrder.objects.get(id_work_order='WO-0001')
ubicacion_origen = orden.origin_location

print(f"Validando stock para {orden}:")

suficiente = True
for line in orden.bill_of_materials.lines.all():
    # Stock disponible
    total_in = InventoryMovement.objects.filter(
        material=line.component,
        location=ubicacion_origen,
        movement_type__symbol__endswith='_IN'
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    total_out = InventoryMovement.objects.filter(
        material=line.component,
        location=ubicacion_origen,
        movement_type__symbol__endswith='_OUT'
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    disponible = total_in - total_out
    
    # Cantidad requerida
    requerido = line.quantity * orden.quantity
    
    # Comparar
    estado = "✓ OK" if disponible >= requerido else "✗ INSUFICIENTE"
    print(f"  {line.component.name}: {requerido} requeridos, {disponible} disponibles {estado}")
    
    if disponible < requerido:
        suficiente = False

if suficiente:
    print("✓ Stock suficiente para producir")
else:
    print("✗ Stock insuficiente")

# Output:
#   Tablero: 20 requeridos, 25 disponibles ✓ OK
#   Pata: 80 requeridos, 100 disponibles ✓ OK
#   Tornillo M6: 320 requeridos, 500 disponibles ✓ OK
# ✓ Stock suficiente para producir
```

---

### Buscar y Filtrar Órdenes:
```python
from manufacturing.models import WorkOrder

# Todas las órdenes
todas = WorkOrder.objects.all()

# Por estado
borradores = WorkOrder.objects.filter(status__symbol='DRAFT')
en_proceso = WorkOrder.objects.filter(status__symbol='IN_PROGRESS')
terminadas = WorkOrder.objects.filter(status__symbol='DONE')
canceladas = WorkOrder.objects.filter(status__symbol='CANCELLED')

# Por BOM (producto)
mesas = WorkOrder.objects.filter(
    bill_of_materials__material__name__icontains='mesa'
)

# Por ubicación origen
bod_mp = WorkOrder.objects.filter(origin_location__code='BOD-MP')

# Órdenes de hoy
from django.utils import timezone
from datetime import timedelta

hoy = timezone.now().date()
ordenes_hoy = WorkOrder.objects.filter(created_at__date=hoy)

# Órdenes de última semana
hace_7_dias = timezone.now() - timedelta(days=7)
ordenes_semana = WorkOrder.objects.filter(created_at__gte=hace_7_dias)

# Ordenar por más recientes
recientes = WorkOrder.objects.all().order_by('-created_at')[:10]
```

---

### Consultas Avanzadas:
```python
from django.db.models import Count, Sum, Avg
from manufacturing.models import WorkOrder, BillOfMaterials

# Órdenes por estado
por_estado = WorkOrder.objects.values('status__name').annotate(
    total=Count('id')
).order_by('-total')

for item in por_estado:
    print(f"{item['status__name']}: {item['total']}")

# BOMs más usados
boms_populares = BillOfMaterials.objects.annotate(
    num_ordenes=Count('workorder')
).order_by('-num_ordenes')[:10]

for bom in boms_populares:
    print(f"{bom.material.name}: {bom.num_ordenes} órdenes")

# Producción total por producto
from materials.models import Material

productos = Material.objects.filter(
    billofmaterials__isnull=False
).annotate(
    total_producido=Sum('billofmaterials__workorder__quantity')
).order_by('-total_producido')

for producto in productos:
    print(f"{producto.name}: {producto.total_producido or 0} unidades producidas")

# Cantidad promedio por orden
promedio = WorkOrder.objects.aggregate(
    promedio_cantidad=Avg('quantity')
)
print(f"Cantidad promedio: {promedio['promedio_cantidad']:.2f}")
```

---

## Notas Importantes

### ⚠️ **Advertencias:**

1. **Validar Stock Antes de Terminar:**
   - Sistema valida automáticamente
   - No permite terminar si hay insuficiencia
   - Mensaje indica qué material falta

2. **No Eliminar BOMs en Uso:**
   - PROTECT impide eliminar BOM con órdenes
   - Usar status o desactivar en lugar de eliminar
   - Mantener historial de producción

3. **Configurar Tipos de Movimiento:**
   - PRODUCTION_IN y PRODUCTION_OUT deben existir
   - Ejecutar `init_movement_types` antes de usar
   - Sin ellos, terminar producción falla

4. **Ubicaciones Requeridas:**
   - origin_location: De donde sacar MP
   - destination_location: Donde poner PT
   - Si no se especifican, usa ubicación por defecto
   - Debe existir al menos una ubicación

5. **Cancelar Orden Terminada:**
   - Revierte inventario (elimina movimientos)
   - NO revierte asientos contables automáticamente
   - Considerar impacto en contabilidad

6. **Contabilidad Puede Fallar:**
   - Si falla contabilidad, orden se termina igual
   - Mensaje de advertencia al usuario
   - Revisar logs para detalles

---

### 💡 **Tips:**

1. **Diseñar BOMs Correctamente:**
   - Incluir TODOS los componentes necesarios
   - Cantidades precisas
   - Unidades correctas
   - Revisar antes de producir

2. **Usar Ubicaciones Dedicadas:**
   - BOD-MP: Bodega Materias Primas
   - BOD-PT: Bodega Productos Terminados
   - BOD-WIP: Productos en Proceso (opcional)
   - Facilita control y trazabilidad

3. **Iniciar Antes de Terminar:**
   - Flujo: DRAFT → IN_PROGRESS → DONE
   - Permite tracking de órdenes activas
   - Mejor control de producción

4. **Revisar Movimientos Generados:**
   - Verificar que cantidades sean correctas
   - Validar ubicaciones
   - Confirmar referencias

5. **Mantener Historial:**
   - No eliminar órdenes DONE
   - Usar CANCELLED para anular
   - Facilita auditoría y análisis

6. **Validar Stock Regularmente:**
   - Antes de crear órdenes grandes
   - Previene problemas al terminar
   - Planificar compras si es necesario

---

### 📊 **Mejores Prácticas:**

1. **Flujo Completo:**
   - Crear BOM → Crear Orden → Iniciar → Terminar
   - No saltar estados
   - Validar en cada paso

2. **BOMs Versionados:**
   ```python
   # Buena práctica: incluir versión
   BOM-MESA-001-V1
   BOM-MESA-001-V2
   # Permite evolución sin perder historial
   ```

3. **Documentar Cambios en BOM:**
   - Registrar qué cambió
   - Por qué cambió
   - Cuándo cambió
   - Quién lo cambió

4. **Revisar Costos:**
   - Calcular costo de MP
   - Comparar con precio de venta
   - Validar rentabilidad

5. **Control de Calidad:**
   - Verificar PT antes de mover a destino
   - Agregar campos de QC si es necesario
   - Registrar defectos/desperdicios

6. **Planificación de Producción:**
   - Crear órdenes según demanda
   - Considerar capacidad de producción
   - Optimizar tamaños de lote

---

### 🔧 **Mantenimiento:**

1. **Auditoría de Órdenes:**
   ```python
   # Órdenes en proceso hace más de 7 días
   from datetime import timedelta
   from django.utils import timezone
   
   hace_7_dias = timezone.now() - timedelta(days=7)
   
   antiguas = WorkOrder.objects.filter(
       status__symbol='IN_PROGRESS',
       updated_at__lt=hace_7_dias
   )
   
   print(f"Órdenes en proceso hace más de 7 días: {antiguas.count()}")
   ```

2. **Verificar BOMs sin Componentes:**
   ```python
   from django.db.models import Count
   
   sin_componentes = BillOfMaterials.objects.annotate(
       num_lines=Count('lines')
   ).filter(num_lines=0)
   
   print(f"BOMs sin componentes: {sin_componentes.count()}")
   ```

3. **Órdenes sin Ubicaciones:**
   ```python
   sin_ubicacion = WorkOrder.objects.filter(
       Q(origin_location__isnull=True) |
       Q(destination_location__isnull=True)
   )
   
   print(f"Órdenes sin ubicación: {sin_ubicacion.count()}")
   ```

4. **Consistencia de Movimientos:**
   ```python
   # Órdenes DONE sin movimientos
   from inventory.models import InventoryMovement
   
   terminadas = WorkOrder.objects.filter(status__symbol='DONE')
   
   for orden in terminadas:
       movimientos = InventoryMovement.objects.filter(
           reference=orden.id_work_order
       ).count()
       
       if movimientos == 0:
           print(f"⚠️ {orden.id_work_order} DONE pero sin movimientos")
   ```

---

## Resumen Técnico

**Modelos:** 4 (WorkOrderStatus, BillOfMaterials, BillOfMaterialsLine, WorkOrder)  
**Vistas:** 3 (list con Kanban, form, detail)  
**URLs:** 3  
**Estados:** 4 (DRAFT, IN_PROGRESS, DONE, CANCELLED)  
**Acciones POST:** 3 (start, finish, cancel)  

**Integraciones:**
- materials.Material (productos y componentes)
- materials.Unit (unidades de medida)
- inventory.InventoryLocation (ubicaciones)
- inventory.utils (movimientos de inventario)
- accounting.utils (asientos contables)
- users.User (auditoría)

**Funciones de Utilidad Externas:**
- `create_inventory_movements_for_production_order(production_order, user)` - inventory.utils
- `create_entry_for_production(work_order, user)` - accounting.utils
- `get_default_inventory_location()` - inventory.utils

**Tipos de Movimiento Requeridos:**
- PRODUCTION_OUT (consumo de materias primas)
- PRODUCTION_IN (entrada de productos terminados)

**Validaciones Críticas:**
- Stock suficiente de componentes
- Ubicaciones configuradas
- Tipos de movimiento existentes
- BOM válido con componentes
