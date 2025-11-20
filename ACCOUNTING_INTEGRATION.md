# 📊 INTEGRACIÓN AUTOMÁTICA DE ASIENTOS CONTABLES

## ✅ ESTADO: COMPLETADO

El módulo de contabilidad ahora genera **asientos contables automáticos** cada vez que se ejecutan operaciones en los módulos de **Compras**, **Ventas**, **Producción** e **Inventario**.

---

## 🔄 FUNCIONAMIENTO AUTOMÁTICO

### 1️⃣ COMPRAS - RECEPCIÓN DE MATERIALES

**Cuándo:** Al marcar una orden de compra como "Recibida"

**Asiento generado:**
```
Débito:  Inventario (1.1.05)           $XXX.XX
Crédito: Cuentas por Pagar (2.1.01)    $XXX.XX
```

**Ubicación del código:**
- Archivo: `purchases/views.py`
- Función: `purchase_order_detail_view()`
- Líneas: ~107-121

**Flujo:**
1. Usuario hace clic en "Recibir" en una orden de compra
2. Sistema actualiza cantidades recibidas
3. Sistema crea movimientos de inventario (PURCHASE_IN)
4. **🆕 Sistema crea asiento contable automático**
5. Estado cambia a RECEIVED

**Cuentas utilizadas:**
- **1.1.05** - Inventario (Activo) - **DÉBITO**
- **2.1.01** - Cuentas por Pagar (Pasivo) - **CRÉDITO**

---

### 2️⃣ VENTAS - ENTREGA DE PRODUCTOS

**Cuándo:** Al marcar una orden de venta como "Entregada"

**Asiento generado:**
```
Débito:  Cuentas por Cobrar (1.1.03)   $XXX.XX
Crédito: Ingresos por Ventas (4.1.01)  $XXX.XX
```

**Ubicación del código:**
- Archivo: `sales/views.py`
- Función: `sales_order_detail_view()`
- Líneas: ~355-369

**Flujo:**
1. Usuario hace clic en "Entregar" en una orden de venta
2. Sistema valida stock disponible
3. Sistema crea movimientos de inventario (SALE_OUT)
4. Sistema actualiza cantidades entregadas
5. **🆕 Sistema crea asiento contable automático**
6. Estado cambia a DELIVERED

**Cuentas utilizadas:**
- **1.1.03** - Cuentas por Cobrar (Activo) - **DÉBITO**
- **4.1.01** - Ingresos por Ventas (Ingreso) - **CRÉDITO**

> **Nota:** En el futuro se agregará un segundo asiento para registrar el costo de ventas:
> ```
> Débito:  Costo de Ventas (5.1.01)
> Crédito: Inventario (1.1.05)
> ```

---

### 3️⃣ PRODUCCIÓN - ORDEN TERMINADA

**Cuándo:** Al marcar una orden de trabajo como "Terminada"

**Asiento generado:**
```
Débito:  Inventario Producto Terminado (1.1.06)  $XXX.XX
Crédito: Inventario Materia Prima (1.1.05)       $XXX.XX
```

**Ubicación del código:**
- Archivo: `manufacturing/views.py`
- Función: `work_order_list_view()`
- Líneas: ~85-98

**Flujo:**
1. Usuario hace clic en "Terminar" en una orden de trabajo
2. Sistema valida stock suficiente de componentes
3. Sistema crea movimientos de inventario:
   - PRODUCTION_OUT para materias primas consumidas
   - PRODUCTION_IN para producto terminado generado
4. **🆕 Sistema crea asiento contable automático**
5. Estado cambia a DONE

**Cuentas utilizadas:**
- **1.1.06** - Inventario Producto Terminado (Activo) - **DÉBITO**
- **1.1.05** - Inventario Materia Prima (Activo) - **CRÉDITO**

> **Nota:** Por ahora el costo se estima en base a la cantidad producida. En el futuro se calculará el costo real basado en materiales consumidos y costos de mano de obra.

---

### 4️⃣ INVENTARIO - AJUSTES MANUALES

**Cuándo:** Al crear un ajuste de inventario (entrada o salida)

**Asiento generado (AJUSTE POSITIVO - ADJUSTMENT_IN):**
```
Débito:  Inventario (1.1.05)                  $XXX.XX
Crédito: Ganancia por Ajuste (5.1.05)         $XXX.XX
```

**Asiento generado (AJUSTE NEGATIVO - ADJUSTMENT_OUT):**
```
Débito:  Pérdida por Ajuste (5.1.05)          $XXX.XX
Crédito: Inventario (1.1.05)                  $XXX.XX
```

**Ubicación del código:**
- Archivo: `inventory/views.py`
- Función: `inventory_adjustment_view()`
- Líneas: ~352-365

**Flujo:**
1. Usuario accede a "Ajuste de Inventario"
2. Usuario selecciona material, cantidad y tipo (entrada/salida)
3. Sistema crea movimiento de inventario (ADJUSTMENT_IN o ADJUSTMENT_OUT)
4. **🆕 Sistema crea asiento contable automático**
5. Sistema muestra confirmación

**Cuentas utilizadas:**
- **1.1.05** - Inventario (Activo)
- **5.1.05** - Ajustes de Inventario (Gasto/Ingreso)

---

## 📋 PLAN DE CUENTAS REQUERIDO

Para que el sistema funcione correctamente, debes tener estas cuentas creadas en tu **Plan de Cuentas**:

### Cuentas Activo
- **1.1.03** - Cuentas por Cobrar
- **1.1.05** - Inventario / Materia Prima
- **1.1.06** - Inventario Producto Terminado

### Cuentas Pasivo
- **2.1.01** - Cuentas por Pagar

### Cuentas Ingreso
- **4.1.01** - Ingresos por Ventas

### Cuentas Gasto
- **5.1.01** - Costo de Ventas (futuro)
- **5.1.05** - Ajustes de Inventario

---

## 🔧 CONFIGURACIÓN DE CUENTAS

### Opción 1: Crear cuentas manualmente

1. Ir a **Admin** → **Accounting** → **Account Accounts**
2. Crear cada cuenta con su código correspondiente
3. Asignar naturaleza (Debit/Credit)
4. Asignar tipo (Activo, Pasivo, Ingreso, Gasto)

### Opción 2: Usar comando de inicialización (si existe)

```bash
python manage.py create_chart_of_accounts
```

---

## ⚙️ FUNCIONES UTILITARIAS

Las funciones de generación automática están en: `accounting/utils.py`

### Funciones principales:

#### 1. `create_entry_for_purchase(purchase_order, user=None)`
Crea asiento para recepción de compra.

#### 2. `create_entry_for_sale(sales_order, user=None)`
Crea asiento para entrega de venta.

#### 3. `create_entry_for_production(work_order, user=None)`
Crea asiento para producción terminada.

#### 4. `create_entry_for_inventory_adjustment(movement, user=None)`
Crea asiento para ajustes de inventario.

### Funciones auxiliares:

#### `post_journal_entry(journal_entry_id)`
Contabiliza un asiento (cambia estado de DRAFT a POSTED).

#### `cancel_journal_entry(journal_entry_id)`
Anula un asiento (cambia estado a CANCELLED).

---

## 📊 ESTADOS DE ASIENTOS

Todos los asientos se crean en estado **DRAFT** (Borrador) por defecto.

### Estados disponibles:
- **DRAFT**: Borrador - Se puede editar y eliminar
- **POSTED**: Contabilizado - No se puede editar, afecta reportes
- **CANCELLED**: Anulado - No afecta reportes

### Contabilizar asiento:

**Opción 1: Admin**
1. Ir a **Admin** → **Accounting** → **Journal Entries**
2. Seleccionar el asiento
3. Hacer clic en "Contabilizar"

**Opción 2: Código**
```python
from accounting.utils import post_journal_entry

post_journal_entry('JE-000001')
```

---

## 🔍 VALIDACIONES

El sistema valiza automáticamente:

✅ **Balance:** Débitos = Créditos
✅ **Duplicados:** No crear asiento si ya existe para el mismo documento
✅ **Cuentas:** Las cuentas deben existir en el plan de cuentas
✅ **Montos:** No se permiten valores negativos
✅ **Débito/Crédito:** Una línea no puede tener ambos

---

## 🧪 PRUEBAS

### Probar Compras:
1. Crear una orden de compra
2. Marcarla como "Recibida"
3. Verificar en Admin → Accounting → Journal Entries
4. Debe aparecer un asiento JE-XXXXXX con:
   - Operation Type: PURCHASE
   - Module: PURCHASES
   - Reference: ID de la orden de compra
   - 2 líneas (Débito Inventario, Crédito Cuentas por Pagar)

### Probar Ventas:
1. Crear una orden de venta
2. Confirmarla
3. Marcarla como "Entregada"
4. Verificar asiento con:
   - Operation Type: SALE
   - Module: SALES
   - Reference: ID de la orden de venta

### Probar Producción:
1. Crear una orden de trabajo
2. Marcarla como "Terminada"
3. Verificar asiento con:
   - Operation Type: PRODUCTION
   - Module: MANUFACTURING
   - Reference: ID de la orden de trabajo

### Probar Ajustes:
1. Ir a Inventario → Ajuste
2. Crear ajuste de entrada o salida
3. Verificar asiento con:
   - Operation Type: ADJUSTMENT
   - Module: INVENTORY
   - Reference: ID del movimiento

---

## 🚨 MANEJO DE ERRORES

Si algo falla al crear un asiento contable:

1. **La operación NO se cancela** - La transacción principal continúa
2. **Se registra en el log** - Revisar logs del sistema
3. **No se muestra error al usuario** - Para no interrumpir el flujo

### Revisar logs:

Los errores se registran en el logger de Django:

```python
logger.error(f'Error al crear asiento contable para compra {order_id}: {str(e)}')
```

### Crear asiento manualmente:

Si un asiento no se creó automáticamente:

```python
from accounting.utils import create_entry_for_purchase
from purchases.models import PurchaseOrder

order = PurchaseOrder.objects.get(id_purchase_order='PO-20250101-0001')
journal_entry = create_entry_for_purchase(order)
```

---

## 📈 FUTURAS MEJORAS

### 1. Costeo de Inventario
- Implementar FIFO, LIFO o Promedio Ponderado
- Registrar costo real en ventas
- Calcular costo real en producción

### 2. Asientos de Costo en Ventas
- Agregar segundo asiento:
  ```
  Débito:  Costo de Ventas
  Crédito: Inventario
  ```

### 3. Automatización Completa
- Contabilizar asientos automáticamente (cambiar de DRAFT a POSTED)
- Generar asientos para pagos y cobros
- Generar asientos para devoluciones

### 4. Reportes Contables
- Balance General
- Estado de Resultados
- Libro Mayor
- Libro Diario

---

## 📞 SOPORTE

Si tienes problemas con la integración contable:

1. Verificar que todas las cuentas existen
2. Revisar logs del sistema
3. Verificar que los asientos están en estado DRAFT
4. Contabilizar asientos manualmente si es necesario

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [x] Modelos JournalEntry y JournalEntryLine creados
- [x] Admin interface configurado
- [x] Funciones utilitarias creadas
- [x] Integración en módulo de Compras
- [x] Integración en módulo de Ventas
- [x] Integración en módulo de Producción
- [x] Integración en módulo de Inventario
- [x] Validaciones de balance
- [x] Manejo de errores
- [x] Logging implementado
- [x] Documentación completa

---

**Fecha de implementación:** 2025-01-16

**Desarrollador:** GitHub Copilot

**Versión:** 1.0
