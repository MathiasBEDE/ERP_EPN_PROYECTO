# 📦 Módulo de Inventario (Inventory)

## Descripción General
Módulo encargado de la gestión completa de inventario, incluyendo ubicaciones de almacenamiento, movimientos de entrada/salida, control de stock, ajustes y trazabilidad completa de materiales. Integrado con compras, ventas, manufactura y contabilidad.

---

## Modelos Principales

### 1. **MovementType** (Tipo de Movimiento)
Catálogo de tipos de movimientos de inventario (entradas y salidas).

**Campos:**
- `name`: Nombre del tipo - CharField(100, unique=True)
- `symbol`: Símbolo único - CharField(10, unique=True)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, SET_NULL, null=True)

**Métodos:**
- `__str__()`: Retorna formato "Name (Symbol)"
  ```python
  def __str__(self):
      return f"{self.name} ({self.symbol})"
  ```

**Tabla de Base de Datos:** `movement_type`

**Tipos del Sistema:**

**Entradas (_IN):**
```
- PURCHASE_IN: Entrada por compra
- PRODUCTION_IN: Entrada por producción (productos terminados)
- ADJUSTMENT_IN: Ajuste de inventario (entrada)
```

**Salidas (_OUT):**
```
- SALE_OUT: Salida por venta
- PRODUCTION_OUT: Salida por producción (consumo de materias primas)
- ADJUSTMENT_OUT: Ajuste de inventario (salida)
```

**Convención:**
- Tipos terminados en `_IN`: Incrementan stock
- Tipos terminados en `_OUT`: Decrementan stock

---

### 2. **InventoryLocation** (Ubicación de Inventario)
Representa ubicaciones físicas de almacenamiento.

**Campos:**
- `id_location`: Código único ERP - CharField(50, unique=True)
- `name`: Nombre de la ubicación - CharField(200)
- `code`: Código corto - CharField(20)
- `main_location`: Ubicación principal (por defecto) - BooleanField(default=False)
- `location`: Dirección física - CharField(300)
- `status`: Estado activo/inactivo - BooleanField(default=True)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, SET_NULL, null=True)

**Métodos:**
- `__str__()`: Retorna formato "Code - Name"
  ```python
  def __str__(self):
      return f"{self.code} - {self.name}"
  ```

**Tabla de Base de Datos:** `location_inventory`

**Índices:**
- `id_location` (unique, búsqueda rápida)
- `name` (ordenamiento alfabético)

**Related Names:**
- `inventorymovement_set`: Movimientos en esta ubicación
- `purchase_orders` (desde PurchaseOrder): Órdenes con destino aquí
- `work_orders_origin` (desde WorkOrder): Órdenes que consumen de aquí
- `work_orders_destination` (desde WorkOrder): Órdenes que producen aquí
- `sales_orders` (desde SalesOrder): Órdenes con origen aquí

**Ejemplo de Ubicaciones:**
```
BOD-MP: Bodega Materias Primas
BOD-PT: Bodega Productos Terminados
BOD-WIP: Bodega Productos en Proceso
ALM-01: Almacén Principal
RACK-A1: Rack A, Nivel 1
```

---

### 3. **InventoryMovement** (Movimiento de Inventario)
Registra cada transacción de entrada o salida de materiales.

**Campos:**
- `id_inventory_movement`: Código único (ej: INV-20251123143022-1234) - CharField(50, unique=True)
- `location`: Ubicación del movimiento - ForeignKey(InventoryLocation, PROTECT)
- `material`: Material movido - ForeignKey(Material, PROTECT)
- `quantity`: Cantidad (siempre positiva) - IntegerField
- `unit_type`: Unidad de medida - ForeignKey(Unit, PROTECT)
- `movement_type`: Tipo de movimiento - ForeignKey(MovementType, PROTECT)
- `movement_date`: Fecha/hora del movimiento - DateTimeField(auto_now_add=True)
- `reference`: Referencia al documento origen - CharField(100, null=True, blank=True)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, SET_NULL, null=True)

**Métodos:**

- `__str__()`: Retorna formato "ID - Material Name"
  ```python
  def __str__(self):
      return f"{self.id_inventory_movement} - {self.material.name}"
  ```

- `clean()`: Validaciones de integridad
  ```python
  def clean(self):
      """
      Validaciones:
      1. Cantidad debe ser positiva (> 0)
      2. Unidad debe coincidir con la unidad del material
      3. Para salidas, debe haber stock suficiente
      """
      errors = {}
      
      # Validación 1: Cantidad positiva
      if self.quantity is None or self.quantity <= 0:
          errors['quantity'] = 'La cantidad debe ser un número positivo mayor a cero.'
      
      # Validación 2: Coherencia de unidad
      if self.unit_type and self.material:
          if self.unit_type != self.material.unit:
              errors['unit_type'] = 'La unidad seleccionada no coincide con la unidad base del material.'
      
      # Validación 3: Stock suficiente para salidas
      if self.movement_type and self.movement_type.symbol.endswith('_OUT'):
          # Calcular stock actual
          current_stock = InventoryMovement.objects.filter(
              material=self.material,
              location=self.location
          ).exclude(pk=self.pk if self.pk else None).aggregate(
              total=Sum(
                  Case(
                      When(movement_type__symbol__endswith='_OUT', then=-F('quantity')),
                      default=F('quantity'),
                      output_field=DecimalField()
                  )
              )
          )['total'] or 0
          
          if self.quantity > current_stock:
              errors['quantity'] = (
                  f'Stock insuficiente en {self.location.name}. '
                  f'Disponible: {current_stock} {self.unit_type.symbol}'
              )
      
      if errors:
          raise ValidationError(errors)
  ```

**Tabla de Base de Datos:** `inventory_movements`

**Índices:**
- `id_inventory_movement` (unique, búsqueda rápida)
- `-created_at` (movimientos más recientes primero)

**Cálculo de Stock:**
```python
# Stock de un material en una ubicación:
entradas = Sum(quantity WHERE movement_type endswith '_IN')
salidas = Sum(quantity WHERE movement_type endswith '_OUT')
stock = entradas - salidas
```

**Convenciones:**
- `quantity` siempre es positiva
- El signo (entrada/salida) se determina por `movement_type.symbol`
- `reference` vincula con documentos origen (PO-0001, SO-0001, WO-0001)

---

## Formularios (Forms)

### **InventoryAdjustmentForm**
Formulario para registrar ajustes manuales de inventario.

**Campos Incluidos:**
```python
fields = ['material', 'location', 'movement_type', 'quantity', 'unit_type', 'reference']
```

**Widgets:**
- `material`: Select con clases Tailwind
- `unit_type`: HiddenInput (se asigna automáticamente)
- `location`: Select
- `movement_type`: Select (solo ADJUSTMENT_IN/OUT)
- `quantity`: NumberInput (min=0.01, step=0.01)
- `reference`: TextInput con placeholder

**Validaciones:**
- Solo permite tipos ADJUSTMENT_IN y ADJUSTMENT_OUT
- Materiales activos ordenados por nombre
- Ubicaciones activas ordenadas por nombre
- unit_type se asigna automáticamente según el material

---

## URLs Disponibles

```python
# Dashboard
/inventory/                              # Dashboard principal

# Movimientos
/inventory/movements/                    # Lista de movimientos

# Stock
/inventory/stock/                        # Consulta de stock actual

# Ajustes
/inventory/adjustment/new/               # Registrar ajuste manual
```

---

## Vistas (Views)

### 1. **inventory_dashboard**
Vista principal del dashboard de inventario con estadísticas.

**URL:** `/inventory/`  
**Método:** GET  
**Decorador:** `@login_required`

**Estadísticas Mostradas:**
- Total de movimientos registrados
- Total de ubicaciones activas
- Movimientos recientes (últimos 5)
- Movimientos por ubicación (top 5)

**Contexto del Template:**
```python
{
    'total_movements': <conteo total>,
    'total_locations': <conteo ubicaciones activas>,
    'recent_movements': <últimos 5 movimientos>,
    'movements_by_location': <top 5 ubicaciones por actividad>
}
```

---

### 2. **inventory_movement_list_view**
Lista paginada de movimientos con filtros avanzados y exportación CSV.

**URL:** `/inventory/movements/`  
**Método:** GET  
**Decorador:** Ninguno (debería tener `@login_required`)

**Parámetros GET (Filtros):**

- `q`: Búsqueda general (ID movimiento, ID material, nombre material, referencia)
- `material`: Filtrar por material (ID o nombre contiene)
- `location`: Filtrar por ubicación (ID numérico)
- `type`: Filtrar por tipo de movimiento (symbol)
- `date_from`: Fecha desde (YYYY-MM-DD)
- `date_to`: Fecha hasta (YYYY-MM-DD)
- `page`: Número de página (10 registros por página)
- `export`: Si es "csv", exporta resultados

**Funcionalidades:**
- ✅ Paginación (10 movimientos por página)
- ✅ 6 filtros combinables
- ✅ Búsqueda por texto múltiple
- ✅ Exportación CSV con filtros aplicados
- ✅ Optimización con select_related()
- ✅ Ordenamiento por fecha descendente

**Exportación CSV:**
- Content-Type: `text/csv; charset=utf-8`
- Filename: `movimientos_inventario.csv`
- BOM: `\ufeff` para Excel
- Separador: coma (,)
- Columnas (11):
  - ID Movimiento
  - Material ID
  - Material Nombre
  - Ubicación Código
  - Ubicación Nombre
  - Cantidad (con signo según tipo)
  - Unidad
  - Tipo
  - Fecha (YYYY-MM-DD HH:MM:SS)
  - Referencia
  - Creado Por

**Nota sobre Cantidad en CSV:**
- Salidas (_OUT): cantidad con prefijo "-"
- Entradas (_IN): cantidad sin prefijo

**Contexto del Template:**
```python
{
    'page_obj': <Page object>,
    'movements': <movimientos en página actual>,
    'locations': <ubicaciones activas>,
    'movement_types': <todos los tipos>,
    'filters': {
        'q': <búsqueda>,
        'material': <filtro material>,
        'location': <filtro ubicación>,
        'type': <filtro tipo>,
        'date_from': <fecha desde>,
        'date_to': <fecha hasta>
    },
    'total_count': <total de movimientos filtrados>
}
```

**Ejemplos de uso:**
```
# Todos los movimientos
/inventory/movements/

# Movimientos de un material
/inventory/movements/?material=PROD-001

# Movimientos en una ubicación
/inventory/movements/?location=1

# Movimientos de compra
/inventory/movements/?type=PURCHASE_IN

# Rango de fechas
/inventory/movements/?date_from=2024-01-01&date_to=2024-12-31

# Búsqueda por referencia
/inventory/movements/?q=PO-0001

# Exportar filtrado
/inventory/movements/?type=SALE_OUT&export=csv
```

---

### 3. **inventory_stock_view**
Consulta de stock actual por material y ubicación.

**URL:** `/inventory/stock/`  
**Método:** GET  
**Decorador:** Ninguno (debería tener `@login_required`)

**Parámetros GET (Filtros):**
- `q`: Buscar por material (ID o nombre contiene)
- `location`: Filtrar por ubicación (ID numérico)
- `page`: Número de página (10 registros por página)
- `export`: Si es "csv", exporta resultados

**Cálculo de Stock:**
```python
# Para cada combinación (material, ubicación, unidad):
stock = 0
for movement in movements:
    if movement.type endswith '_OUT':
        stock -= movement.quantity
    else:  # endswith '_IN'
        stock += movement.quantity

# Solo mostrar si stock != 0
```

**Funcionalidades:**
- ✅ Calcula stock en tiempo real desde movimientos
- ✅ Agrupa por (material, ubicación, unidad)
- ✅ Excluye cantidades en cero
- ✅ Paginación (10 entradas por página)
- ✅ Filtros por material y ubicación
- ✅ Exportación CSV
- ✅ Ordenado por material y luego ubicación

**Exportación CSV:**
- Filename: `stock_inventario.csv`
- Columnas (6):
  - ID Material
  - Material
  - Código Ubicación
  - Ubicación
  - Cantidad
  - Unidad

**Contexto del Template:**
```python
{
    'page_obj': <Page object>,
    'stocks': <entradas de stock en página actual>,
    'locations': <ubicaciones activas>,
    'filters': {
        'q': <búsqueda material>,
        'location': <filtro ubicación>
    },
    'total_count': <total de entradas de stock>
}
```

**Ejemplos de uso:**
```
# Todo el stock
/inventory/stock/

# Stock de un material
/inventory/stock/?q=PROD-001

# Stock en una ubicación
/inventory/stock/?location=1

# Exportar todo
/inventory/stock/?export=csv
```

---

### 4. **inventory_adjustment_view**
Formulario para registrar ajustes manuales de inventario.

**URL:** `/inventory/adjustment/new/`  
**Métodos:** GET, POST  
**Decorador:** Ninguno (debería tener `@login_required`)

**Flujo GET:**
1. Crea formulario vacío `InventoryAdjustmentForm`
2. Renderiza template con formulario

**Flujo POST:**

**Parámetros POST:**
- `material`: ID del material (int)
- `location`: ID de ubicación (int)
- `movement_type`: ID de tipo (ADJUSTMENT_IN o ADJUSTMENT_OUT)
- `quantity`: Cantidad (decimal > 0)
- `reference`: Referencia opcional (string)

**Proceso Completo:**

1. **Asignar unit_type automáticamente:**
   ```python
   if 'material' in form.data:
       material = Material.objects.get(pk=material_id)
       form.instance.unit_type = material.unit
   ```

2. **Validar formulario**

3. **Generar ID único:**
   ```python
   timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
   unique_id = f"INV-{timestamp}-{random.randint(1000, 9999)}"
   ```
   Ejemplo: `INV-20251123143022-5678`

4. **Asignar datos:**
   ```python
   movement.id_inventory_movement = unique_id
   movement.unit_type = movement.material.unit
   movement.created_by = request.user
   ```

5. **Validar integridad:**
   ```python
   movement.full_clean()  # Ejecuta clean() del modelo
   ```
   - Valida cantidad positiva
   - Valida unidad coincidente
   - Valida stock suficiente (si es salida)

6. **Guardar movimiento:**
   ```python
   movement.save()
   ```

7. **Crear asiento contable automático:**
   ```python
   journal_entry = create_entry_for_inventory_adjustment(
       movement,
       user=request.user
   )
   ```
   
   **Asientos Generados:**
   
   **Ajuste de Entrada (ADJUSTMENT_IN):**
   ```
   Débito:  Inventario (Activo)       $XXX.XX
   Crédito: Ajuste de Inventario (OE) $XXX.XX
   ```
   
   **Ajuste de Salida (ADJUSTMENT_OUT):**
   ```
   Débito:  Ajuste de Inventario (OE) $XXX.XX
   Crédito: Inventario (Activo)       $XXX.XX
   ```

8. **Mensajes al usuario:**
   - ✅ "Ajuste de inventario registrado exitosamente: INV-XXX - Material (entrada/salida de X unid)"
   - ✅ "Asiento contable JE-XXXX generado automáticamente."
   - ⚠️ "⚠️ AJUSTE REGISTRADO pero fallo contable: <error>"

9. **Redirigir a lista de movimientos**

**Validaciones:**
- Cantidad debe ser > 0
- Unidad debe coincidir con material
- Stock suficiente para salidas
- Material debe existir
- Ubicación debe existir
- Tipo debe ser ADJUSTMENT_IN o ADJUSTMENT_OUT

**Mensajes de Error:**
- ❌ "No se pudo registrar el ajuste. Por favor verifique los datos."
- ❌ "Por favor corrija los errores en el formulario."
- ❌ "Stock insuficiente en <ubicación>. Disponible: X unid"
- ❌ "La cantidad debe ser un número positivo mayor a cero."
- ❌ "La unidad seleccionada no coincide con la unidad base del material."

**Contexto del Template:**
```python
{
    'form': <InventoryAdjustmentForm>
}
```

---

## Funciones de Utilidad (utils.py)

### 1. **get_default_inventory_location()**
Obtiene la ubicación de inventario por defecto.

**Retorna:** `InventoryLocation`

**Lógica:**
1. Busca ubicación con `main_location=True` y `status=True`
2. Si no existe, busca primera ubicación con `status=True`
3. Si no existe ninguna, lanza excepción

**Excepciones:**
```python
InventoryLocation.DoesNotExist:
    "No hay ubicaciones de inventario activas en el sistema."
```

**Uso:**
```python
from inventory.utils import get_default_inventory_location

location = get_default_inventory_location()
print(location)  # BOD-01 - Bodega Principal
```

---

### 2. **create_inventory_movements_for_purchase_order(purchase_order, user=None)**
Crea movimientos de inventario al recibir una orden de compra.

**Parámetros:**
- `purchase_order`: Instancia de PurchaseOrder
- `user`: Usuario que realiza la acción (opcional)

**Retorna:** `list` de InventoryMovement creados

**Proceso:**
1. Usa `destination_location` del PO o ubicación por defecto
2. Obtiene tipo PURCHASE_IN
3. Verifica que no existan movimientos duplicados (por reference)
4. Para cada línea del PO:
   - Usa `received_quantity` si > 0, sino `quantity`
   - Genera ID único: `INV-YYYYMMDD-HHMMSS-LINE_ID`
   - Crea movimiento tipo PURCHASE_IN
   - Valida con `full_clean()`
   - Guarda movimiento

**Excepciones:**
```python
InventoryLocation.DoesNotExist: Sin ubicación por defecto
MovementType.DoesNotExist: PURCHASE_IN no existe
ValidationError: Error de validación en movimiento
```

**Ejemplo:**
```python
from inventory.utils import create_inventory_movements_for_purchase_order

movements = create_inventory_movements_for_purchase_order(
    purchase_order=po,
    user=request.user
)
print(f"Creados {len(movements)} movimientos")
```

---

### 3. **create_inventory_movements_for_production_order(production_order, user=None)**
Crea movimientos de inventario al completar una orden de producción.

**Parámetros:**
- `production_order`: Instancia de WorkOrder
- `user`: Usuario que realiza la acción (opcional)

**Retorna:** `list` de InventoryMovement creados

**Proceso:**

1. **Validar ubicaciones:**
   - `origin_location` debe estar definida
   - `destination_location` debe estar definida

2. **Obtener o crear tipos:**
   - PRODUCTION_OUT (consumo MP)
   - PRODUCTION_IN (entrada PT)

3. **Verificar duplicados** por reference

4. **Crear movimientos de salida (consumo MP):**
   ```python
   for component in BOM.lines:
       quantity_consumed = component.quantity × work_order.quantity
       
       Movimiento:
         - ID: INV-{timestamp}-OUT-{line.id}
         - location: origin_location
         - material: component
         - quantity: quantity_consumed
         - unit_type: component.unit
         - movement_type: PRODUCTION_OUT
         - reference: WO-XXXX
   ```

5. **Crear movimiento de entrada (producto terminado):**
   ```python
   Movimiento:
     - ID: INV-{timestamp}-IN-WO{wo.id}
     - location: destination_location
     - material: BOM.material
     - quantity: work_order.quantity
     - unit_type: product.unit
     - movement_type: PRODUCTION_IN
     - reference: WO-XXXX
   ```

6. **Validar cada movimiento con `full_clean()`**

7. **Usar `transaction.atomic()` para atomicidad**

**Excepciones:**
```python
ValueError: origin_location o destination_location no definidos
MovementType.DoesNotExist: PRODUCTION_IN/OUT no existen
ValidationError: Error de validación (stock insuficiente)
```

**Ejemplo:**
```python
from inventory.utils import create_inventory_movements_for_production_order

movements = create_inventory_movements_for_production_order(
    production_order=wo,
    user=request.user
)
print(f"Creados {len(movements)} movimientos")
# Output: Creados 6 movimientos (5 salidas + 1 entrada)
```

---

### 4. **create_inventory_movements_for_sales_order(sales_order, user=None)**
Crea movimientos de inventario al entregar una orden de venta.

**Parámetros:**
- `sales_order`: Instancia de SalesOrder
- `user`: Usuario que realiza la acción (opcional)

**Retorna:** `list` de InventoryMovement creados

**Proceso:**
1. Usa `source_location` del SO o ubicación por defecto
2. Obtiene tipo SALE_OUT
3. Verifica duplicados por reference
4. Para cada línea del SO:
   - Usa `quantity` de la línea
   - Genera ID único: `INV-YYYYMMDD-HHMMSS-LINE_ID`
   - Crea movimiento tipo SALE_OUT
   - Valida con `full_clean()` (incluyendo stock)
   - Si falla validación, aborta toda la operación

**Excepciones:**
```python
InventoryLocation.DoesNotExist: Sin ubicación
MovementType.DoesNotExist: SALE_OUT no existe
ValidationError: Stock insuficiente para la línea X
```

**Nota Crítica:**
- Si hay stock insuficiente en cualquier línea, aborta TODA la entrega
- Mantiene consistencia: o se entrega todo o nada

**Ejemplo:**
```python
from inventory.utils import create_inventory_movements_for_sales_order

try:
    movements = create_inventory_movements_for_sales_order(
        sales_order=so,
        user=request.user
    )
    print(f"Creados {len(movements)} movimientos")
except ValidationError as e:
    print(f"Error: {e}")
```

---

## Flujo de Trabajo Completo

### 1. Configuración Inicial

**Crear Tipos de Movimiento:**
```python
from inventory.models import MovementType

# Entradas
MovementType.objects.create(name='Entrada por Compra', symbol='PURCHASE_IN')
MovementType.objects.create(name='Producto Terminado', symbol='PRODUCTION_IN')
MovementType.objects.create(name='Ajuste de Inventario (Entrada)', symbol='ADJUSTMENT_IN')

# Salidas
MovementType.objects.create(name='Salida por Venta', symbol='SALE_OUT')
MovementType.objects.create(name='Consumo en Producción', symbol='PRODUCTION_OUT')
MovementType.objects.create(name='Ajuste de Inventario (Salida)', symbol='ADJUSTMENT_OUT')
```

**Crear Ubicaciones:**
```python
from inventory.models import InventoryLocation

InventoryLocation.objects.create(
    id_location='LOC-001',
    name='Bodega Principal',
    code='BOD-01',
    main_location=True,  # Ubicación por defecto
    location='Av. Principal 123, Quito',
    status=True
)

InventoryLocation.objects.create(
    id_location='LOC-002',
    name='Bodega Materias Primas',
    code='BOD-MP',
    location='Galpón A, Sector Industrial',
    status=True
)

InventoryLocation.objects.create(
    id_location='LOC-003',
    name='Bodega Productos Terminados',
    code='BOD-PT',
    location='Galpón B, Sector Industrial',
    status=True
)
```

---

### 2. Movimientos Automáticos desde Compras

**Al recibir orden de compra:**
1. Usuario marca orden como DELIVERED en purchases
2. Sistema llama `create_inventory_movements_for_purchase_order()`
3. Movimientos creados automáticamente:
   ```
   PO-0001: Compra de 100 Tornillos
   
   Movimiento: INV-20251123-143022-15
   - Tipo: PURCHASE_IN
   - Material: Tornillos M6
   - Cantidad: 100
   - Ubicación: BOD-MP
   - Referencia: PO-0001
   ```

---

### 3. Movimientos Automáticos desde Producción

**Al terminar orden de producción:**
1. Usuario marca orden como DONE en manufacturing
2. Sistema llama `create_inventory_movements_for_production_order()`
3. Movimientos creados:
   
   **Consumo de MP:**
   ```
   WO-0001: Producir 10 Mesas
   
   Movimientos OUT:
   1. INV-20251123-150000-OUT-5
      - Tipo: PRODUCTION_OUT
      - Material: Tablero
      - Cantidad: 10
      - Ubicación: BOD-MP
   
   2. INV-20251123-150000-OUT-6
      - Tipo: PRODUCTION_OUT
      - Material: Patas
      - Cantidad: 40
      - Ubicación: BOD-MP
   ```
   
   **Entrada de PT:**
   ```
   Movimiento IN:
   3. INV-20251123-150000-IN-WO1
      - Tipo: PRODUCTION_IN
      - Material: Mesa de Oficina
      - Cantidad: 10
      - Ubicación: BOD-PT
   ```

---

### 4. Movimientos Automáticos desde Ventas

**Al entregar orden de venta:**
1. Usuario marca orden como DELIVERED en sales
2. Sistema llama `create_inventory_movements_for_sales_order()`
3. Validación de stock automática
4. Movimientos creados:
   ```
   SO-0001: Venta de 5 Mesas
   
   Movimiento: INV-20251123-160000-20
   - Tipo: SALE_OUT
   - Material: Mesa de Oficina
   - Cantidad: 5
   - Ubicación: BOD-PT
   - Referencia: SO-0001
   ```

---

### 5. Ajustes Manuales

**Inventario Inicial:**
```
1. Ir a /inventory/adjustment/new/
2. Seleccionar:
   - Material: Tornillos M6
   - Ubicación: BOD-MP
   - Tipo: Ajuste (Entrada)
   - Cantidad: 500
   - Referencia: "Inventario inicial"
3. Guardar
4. Sistema genera:
   - Movimiento: INV-20251123143022-5678
   - Asiento contable automático
```

**Corrección por Conteo Físico:**
```
Escenario: Sistema muestra 100 unidades, conteo físico muestra 95

1. Registrar ajuste de salida:
   - Material: Tornillos M6
   - Ubicación: BOD-MP
   - Tipo: Ajuste (Salida)
   - Cantidad: 5
   - Referencia: "Corrección conteo físico 2024-11-23"
2. Stock se ajusta de 100 a 95
```

---

### 6. Consultar Stock

**Ver Stock de un Material:**
```
1. Ir a /inventory/stock/
2. Buscar: "Tornillos M6"
3. Resultado:
   
   Material: Tornillos M6
   ├─ BOD-MP: 495 unid
   └─ BOD-01: 50 unid
   Total: 545 unid
```

**Ver Movimientos de un Material:**
```
1. Ir a /inventory/movements/
2. Filtrar por material: "Tornillos M6"
3. Ver historial completo:
   - 2024-11-20: +500 (ADJUSTMENT_IN) - Inventario inicial
   - 2024-11-21: +100 (PURCHASE_IN) - PO-0001
   - 2024-11-22: -100 (PRODUCTION_OUT) - WO-0001
   - 2024-11-23: -5 (ADJUSTMENT_OUT) - Corrección
```

---

## Integraciones con Otros Módulos

### **Purchases (Compras)**
- **Función:** `create_inventory_movements_for_purchase_order()`
- **Cuándo:** Al marcar PO como DELIVERED
- **Qué hace:** Crea movimientos PURCHASE_IN
- **Ubicación:** destination_location del PO o por defecto

### **Manufacturing (Manufactura)**
- **Función:** `create_inventory_movements_for_production_order()`
- **Cuándo:** Al marcar WO como DONE
- **Qué hace:**
  - Crea movimientos PRODUCTION_OUT (consumo MP)
  - Crea movimiento PRODUCTION_IN (entrada PT)
- **Ubicaciones:**
  - origin_location: de donde sacar MP
  - destination_location: donde poner PT

### **Sales (Ventas)**
- **Función:** `create_inventory_movements_for_sales_order()`
- **Cuándo:** Al marcar SO como DELIVERED
- **Qué hace:** Crea movimientos SALE_OUT
- **Validación:** Stock suficiente, aborta si falta
- **Ubicación:** source_location del SO o por defecto

### **Accounting (Contabilidad)**
- **Función:** `create_entry_for_inventory_adjustment()`
- **Cuándo:** Al registrar ajuste manual
- **Qué hace:** Genera asiento contable automático
- **Cuentas:** Inventario (Activo) ↔ Ajuste de Inventario (OE)

### **Materials (Materiales)**
- `InventoryMovement.material`: FK a Material
- `InventoryMovement.unit_type`: FK a Unit
- Validación: unit_type debe coincidir con material.unit

### **Users (Usuarios)**
- `created_by`: Usuario que creó el movimiento/ubicación
- Control de permisos (login_required)

---

## Reglas de Negocio

### 1. **Cantidades Siempre Positivas**
- Campo `quantity` siempre almacena valores positivos
- El signo (entrada/salida) se determina por `movement_type.symbol`
- En cálculos: `_OUT` se resta, `_IN` se suma

### 2. **Validación de Stock para Salidas**
- TODOS los movimientos _OUT validan stock suficiente
- Cálculo en tiempo real desde movimientos existentes
- Incluye el movimiento actual si es edición (se excluye del cálculo)
- Si falla validación → lanza ValidationError

### 3. **Coherencia de Unidades**
- `unit_type` debe coincidir con `material.unit`
- Se asigna automáticamente en formularios
- Validación en `clean()` del modelo

### 4. **IDs Únicos Generados Automáticamente**
- Formato: `INV-{timestamp}-{random/line_id}`
- Ejemplo: `INV-20251123143022-1234`
- Garantiza unicidad temporal

### 5. **Referencias a Documentos Origen**
- `reference` vincula con documento que generó el movimiento
- Ejemplos: PO-0001, SO-0001, WO-0001
- Permite trazabilidad completa
- Usado para evitar duplicados

### 6. **Ubicación Principal**
- Solo UNA ubicación puede tener `main_location=True`
- Se usa como ubicación por defecto si no se especifica
- Si no existe, se usa primera ubicación activa

### 7. **Prevención de Duplicados**
- Funciones de utilidad verifican `reference` antes de crear
- Si ya existen movimientos con esa referencia → retorna []
- Evita duplicación en caso de doble submit

### 8. **Integridad Referencial**
- `location`: PROTECT (no eliminar ubicación en uso)
- `material`: PROTECT (no eliminar material con movimientos)
- `unit_type`: PROTECT (no eliminar unidad en uso)
- `movement_type`: PROTECT (no eliminar tipo en uso)
- `created_by`: SET_NULL (si se elimina usuario, pone null)

### 9. **Cálculo de Stock en Tiempo Real**
- Stock NO se almacena, se calcula desde movimientos
- Ventajas:
  - Historial completo
  - Auditoría total
  - Recalculable en cualquier momento
  - Trazabilidad completa

---

## Ejemplos de Código

### Crear Movimiento Manualmente:
```python
from inventory.models import InventoryMovement, InventoryLocation, MovementType
from materials.models import Material
from django.utils import timezone
import random

# Obtener referencias
material = Material.objects.get(id_material='PROD-001')
location = InventoryLocation.objects.get(code='BOD-01')
movement_type = MovementType.objects.get(symbol='ADJUSTMENT_IN')

# Generar ID único
timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
unique_id = f"INV-{timestamp}-{random.randint(1000, 9999)}"

# Crear movimiento
movement = InventoryMovement.objects.create(
    id_inventory_movement=unique_id,
    location=location,
    material=material,
    quantity=100,
    unit_type=material.unit,
    movement_type=movement_type,
    reference='Inventario inicial',
    created_by=request.user
)

print(f"Movimiento creado: {movement}")
```

---

### Consultar Stock de un Material:
```python
from django.db.models import Sum, F, Case, When, DecimalField
from inventory.models import InventoryMovement
from materials.models import Material

material = Material.objects.get(id_material='PROD-001')

# Stock total (todas las ubicaciones)
stock_total = InventoryMovement.objects.filter(
    material=material
).aggregate(
    total=Sum(
        Case(
            When(movement_type__symbol__endswith='_OUT', then=-F('quantity')),
            default=F('quantity'),
            output_field=DecimalField()
        )
    )
)['total'] or 0

print(f"Stock total de {material.name}: {stock_total} {material.unit.symbol}")

# Stock por ubicación
from collections import defaultdict

stock_por_ubicacion = defaultdict(int)

movimientos = InventoryMovement.objects.filter(
    material=material
).select_related('location', 'movement_type')

for mov in movimientos:
    signo = -1 if mov.movement_type.symbol.endswith('_OUT') else 1
    stock_por_ubicacion[mov.location.name] += signo * mov.quantity

print("\nStock por ubicación:")
for ubicacion, cantidad in stock_por_ubicacion.items():
    if cantidad > 0:
        print(f"  {ubicacion}: {cantidad} {material.unit.symbol}")
```

---

### Buscar Movimientos con Filtros:
```python
from inventory.models import InventoryMovement
from django.db.models import Q
from datetime import datetime, timedelta

# Movimientos de un material
material_id = 'PROD-001'
movs_material = InventoryMovement.objects.filter(
    Q(material__id_material=material_id) |
    Q(material__name__icontains='mesa')
)

# Movimientos en una ubicación
movs_ubicacion = InventoryMovement.objects.filter(
    location__code='BOD-01'
)

# Movimientos de compras
movs_compras = InventoryMovement.objects.filter(
    movement_type__symbol='PURCHASE_IN'
)

# Movimientos de última semana
hace_7_dias = datetime.now() - timedelta(days=7)
movs_recientes = InventoryMovement.objects.filter(
    movement_date__gte=hace_7_dias
)

# Movimientos de una referencia
movs_po = InventoryMovement.objects.filter(
    reference='PO-0001'
)

# Combinar filtros
movs_filtrados = InventoryMovement.objects.filter(
    location__code='BOD-01',
    movement_type__symbol__endswith='_IN',
    movement_date__gte=hace_7_dias
).order_by('-movement_date')
```

---

### Validar Stock Antes de Operación:
```python
from django.db.models import Sum, F, Case, When, DecimalField
from inventory.models import InventoryMovement

def verificar_stock(material, ubicacion, cantidad_requerida):
    """
    Verifica si hay stock suficiente para una salida.
    """
    stock_actual = InventoryMovement.objects.filter(
        material=material,
        location=ubicacion
    ).aggregate(
        total=Sum(
            Case(
                When(movement_type__symbol__endswith='_OUT', then=-F('quantity')),
                default=F('quantity'),
                output_field=DecimalField()
            )
        )
    )['total'] or 0
    
    if cantidad_requerida > stock_actual:
        return False, f"Stock insuficiente. Disponible: {stock_actual}, Requerido: {cantidad_requerida}"
    
    return True, f"Stock suficiente. Disponible: {stock_actual}"

# Uso
from materials.models import Material
from inventory.models import InventoryLocation

material = Material.objects.get(id_material='PROD-001')
ubicacion = InventoryLocation.objects.get(code='BOD-01')

suficiente, mensaje = verificar_stock(material, ubicacion, 50)
print(mensaje)

if suficiente:
    # Proceder con la operación
    pass
else:
    # Abortar o solicitar más stock
    pass
```

---

### Generar Reporte de Movimientos:
```python
from inventory.models import InventoryMovement
from django.db.models import Count, Sum
from datetime import datetime

# Movimientos por tipo
por_tipo = InventoryMovement.objects.values(
    'movement_type__name'
).annotate(
    total=Count('id'),
    cantidad_total=Sum('quantity')
).order_by('-total')

print("Movimientos por tipo:")
for item in por_tipo:
    print(f"  {item['movement_type__name']}: {item['total']} movimientos, {item['cantidad_total']} unidades")

# Movimientos por ubicación
por_ubicacion = InventoryMovement.objects.values(
    'location__name'
).annotate(
    total=Count('id')
).order_by('-total')

print("\nMovimientos por ubicación:")
for item in por_ubicacion:
    print(f"  {item['location__name']}: {item['total']} movimientos")

# Movimientos del mes
hoy = datetime.now()
primer_dia_mes = hoy.replace(day=1)

movimientos_mes = InventoryMovement.objects.filter(
    movement_date__gte=primer_dia_mes
).count()

print(f"\nMovimientos del mes: {movimientos_mes}")
```

---

### Historial Completo de un Material:
```python
material = Material.objects.get(id_material='PROD-001')

movimientos = InventoryMovement.objects.filter(
    material=material
).select_related(
    'location',
    'movement_type',
    'created_by'
).order_by('movement_date')

print(f"Historial de {material.name}:")
stock_acumulado = 0

for mov in movimientos:
    signo = -1 if mov.movement_type.symbol.endswith('_OUT') else 1
    cantidad_con_signo = signo * mov.quantity
    stock_acumulado += cantidad_con_signo
    
    print(f"{mov.movement_date.strftime('%Y-%m-%d %H:%M')}: "
          f"{'+' if signo > 0 else ''}{cantidad_con_signo} {mov.unit_type.symbol} "
          f"({mov.movement_type.name}) "
          f"en {mov.location.code} "
          f"- Ref: {mov.reference or 'N/A'} "
          f"- Stock: {stock_acumulado}")
```

---

## Notas Importantes

### ⚠️ **Advertencias:**

1. **No Eliminar Movimientos Históricos:**
   - Pérdida de trazabilidad
   - Inconsistencia en cálculos de stock
   - Problemas de auditoría
   - Usar ajustes correctivos en su lugar

2. **Validar Stock SIEMPRE en Salidas:**
   - Sistema valida automáticamente
   - No confiar solo en frontend
   - Puede haber condiciones de carrera

3. **Tipos de Movimiento Requeridos:**
   - PURCHASE_IN, SALE_OUT, PRODUCTION_IN, PRODUCTION_OUT, ADJUSTMENT_IN, ADJUSTMENT_OUT
   - Ejecutar `init_movement_types` antes de usar
   - Sin ellos, operaciones fallan

4. **Ubicaciones Deben Existir:**
   - Al menos una ubicación activa
   - Preferible tener una como `main_location=True`
   - Configurar antes de operar

5. **Cuidado con Ajustes de Salida:**
   - Validan stock suficiente
   - Pueden fallar si no hay existencias
   - Usar ajustes de entrada para corregir

6. **Referencias son Importantes:**
   - Permiten trazabilidad
   - Evitan duplicados
   - Facilitan auditorías
   - Siempre proporcionar cuando sea posible

---

### 💡 **Tips:**

1. **Usar Ubicaciones Específicas:**
   - BOD-MP: Materias Primas
   - BOD-PT: Productos Terminados
   - BOD-WIP: Work In Progress
   - Facilita control y reportes

2. **Convención de Referencias:**
   - Compras: PO-XXXX
   - Ventas: SO-XXXX
   - Producción: WO-XXXX
   - Ajustes: Descripción clara
   - Consistencia facilita búsquedas

3. **Exportar Regularmente:**
   - Backup de movimientos
   - Análisis en Excel/LibreOffice
   - Reconciliación con contabilidad
   - Usar filtros antes de exportar

4. **Revisar Stock Periódicamente:**
   - Conteos físicos mensuales
   - Comparar con sistema
   - Ajustar discrepancias
   - Documentar causas

5. **Optimizar Queries:**
   - Usar `select_related()` para FKs
   - Filtrar antes de calcular
   - Limitar resultados con paginación
   - Índices en campos de búsqueda

6. **Logging de Operaciones:**
   - Registrar operaciones críticas
   - Facilita debugging
   - Auditoría de acciones
   - Identificar patrones de error

---

### 📊 **Mejores Prácticas:**

1. **Inventario Inicial:**
   ```python
   # Al implementar sistema, registrar inventario existente
   for material, cantidad, ubicacion in inventario_fisico:
       crear_ajuste_entrada(material, cantidad, ubicacion, "Inventario inicial")
   ```

2. **Conteos Cíclicos:**
   ```python
   # Realizar conteos periódicos y ajustar
   stock_sistema = calcular_stock(material, ubicacion)
   stock_fisico = contar_fisicamente()
   
   if stock_fisico != stock_sistema:
       diferencia = stock_fisico - stock_sistema
       registrar_ajuste(diferencia, "Conteo cíclico YYYY-MM-DD")
   ```

3. **Trazabilidad Completa:**
   ```python
   # Siempre incluir referencia
   movement.reference = documento_origen
   movement.created_by = usuario_actual
   movement.save()
   ```

4. **Transacciones Atómicas:**
   ```python
   from django.db import transaction
   
   with transaction.atomic():
       # Crear múltiples movimientos
       # Si uno falla, todos se revierten
       for linea in lineas:
           crear_movimiento(linea)
   ```

5. **Validación Antes de Guardar:**
   ```python
   movement.full_clean()  # Valida integridad
   movement.save()        # Guarda solo si es válido
   ```

---

### 🔧 **Mantenimiento:**

1. **Auditoría de Inconsistencias:**
   ```python
   # Movimientos sin referencia (manual)
   sin_ref = InventoryMovement.objects.filter(
       Q(reference__isnull=True) | Q(reference='')
   )
   
   # Movimientos con cantidad cero
   cantidad_cero = InventoryMovement.objects.filter(quantity=0)
   
   # Movimientos con unidad incorrecta
   unidad_incorrecta = InventoryMovement.objects.exclude(
       unit_type=F('material__unit')
   )
   ```

2. **Limpieza de Datos:**
   ```python
   # Eliminar movimientos huérfanos (si es seguro)
   # CUIDADO: Solo si estás seguro
   huerfanos = InventoryMovement.objects.filter(
       reference__isnull=False
   ).exclude(
       reference__in=referencias_validas
   )
   ```

3. **Recalcular Stock:**
   ```python
   # Verificar que cálculo sea correcto
   for material in Material.objects.all():
       stock_calculado = calcular_stock(material)
       print(f"{material.name}: {stock_calculado}")
   ```

4. **Monitoreo de Stock Bajo:**
   ```python
   # Alertas de stock bajo
   stock_minimo = 10
   
   for material in Material.objects.all():
       stock = calcular_stock(material)
       if stock < stock_minimo:
           print(f"⚠️ Stock bajo: {material.name} ({stock} unid)")
   ```

---

## Resumen Técnico

**Modelos:** 3 (MovementType, InventoryLocation, InventoryMovement)  
**Vistas:** 4 (dashboard, movements list, stock, adjustment)  
**URLs:** 4  
**Formularios:** 1 (InventoryAdjustmentForm)  
**Funciones Utilidad:** 4  
**Tipos de Movimiento:** 6 (3 entradas, 3 salidas)  
**Paginación:** 10 registros por página  
**Filtros:** 6 en movements, 2 en stock  
**Exportación:** CSV en movements y stock  
**Validaciones:** Cantidad, unidad, stock suficiente  

**Integraciones:**
- purchases.PurchaseOrder (movimientos automáticos)
- sales.SalesOrder (movimientos automáticos)
- manufacturing.WorkOrder (movimientos automáticos)
- accounting (asientos para ajustes)
- materials.Material, Unit (referencias)
- users.User (auditoría)

**Cálculo de Stock:**
- En tiempo real desde movimientos
- NO almacenado en tabla separada
- Fórmula: SUM(entradas) - SUM(salidas)
- Por (material, ubicación, unidad)

**Validaciones Críticas:**
- Cantidad > 0 siempre
- Unidad coincidente con material
- Stock suficiente para salidas
- Prevención de duplicados por referencia
