# MÓDULO DE CONTABILIDAD - DOCUMENTACIÓN COMPLETA

## 📋 RESUMEN DE IMPLEMENTACIÓN

Se ha implementado exitosamente el módulo de contabilidad completo para el ERP, incluyendo:

✅ **Modelos de Asientos Contables**: `JournalEntry` y `JournalEntryLine`
✅ **Administración Django**: Interfaz completa con inlines
✅ **Utilidades de Integración**: Funciones para generar asientos desde otros módulos
✅ **Validaciones**: Balance de débitos y créditos
✅ **Generación Automática de IDs**: Formato JE-000001, JE-000002, etc.

---

## 🗂️ ESTRUCTURA DEL MÓDULO

### 1. Modelos (`accounting/models.py`)

#### **JournalEntry (Asiento Contable)**

```python
class JournalEntry(models.Model):
    id_journal_entry = CharField(max_length=50, unique=True)  # JE-000001
    date = DateField()
    description = TextField()
    operation_type = CharField(choices=[
        'PURCHASE', 'SALE', 'PRODUCTION', 'ADJUSTMENT', 'TRANSFER', 'MANUAL'
    ])
    reference = CharField(max_length=100)  # ID del documento origen
    module = CharField(choices=[
        'PURCHASES', 'SALES', 'MANUFACTURING', 'INVENTORY', 'ACCOUNTING'
    ])
    currency = ForeignKey(Currency)
    status = CharField(choices=['DRAFT', 'POSTED', 'CANCELLED'])
    created_at, updated_at, created_by = ...
```

**Métodos principales:**
- `generate_journal_entry_id()`: Genera ID secuencial automático
- `get_total_debit()`: Calcula total de débitos
- `get_total_credit()`: Calcula total de créditos
- `is_balanced()`: Verifica si débitos == créditos
- `post()`: Contabiliza el asiento (estado POSTED)
- `cancel()`: Anula el asiento (estado CANCELLED)

#### **JournalEntryLine (Línea de Asiento)**

```python
class JournalEntryLine(models.Model):
    journal_entry = ForeignKey(JournalEntry, related_name='lines')
    account = ForeignKey(AccountAccount)
    description = CharField(max_length=500, blank=True)
    debit = DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = DecimalField(max_digits=15, decimal_places=2, default=0)
    position = IntegerField()
```

**Validaciones:**
- ✅ No permite débito y crédito > 0 simultáneamente
- ✅ Al menos uno debe ser > 0
- ✅ No permite valores negativos

---

## 🔧 FUNCIONES DE UTILIDAD (`accounting/utils.py`)

### 1. **create_journal_entry_for_purchase(purchase_order, user=None)**

Genera asiento contable para una orden de compra.

**Asiento generado:**
```
Débito:  Inventario (Activo)           $XXX.XX
Crédito: Cuentas por Pagar (Pasivo)            $XXX.XX
```

**Uso:**
```python
from accounting.utils import create_journal_entry_for_purchase
from purchases.models import PurchaseOrder

po = PurchaseOrder.objects.get(id_purchase_order='PO-0001')
journal_entry = create_journal_entry_for_purchase(po, request.user)
```

### 2. **create_journal_entry_for_sale(sales_order, user=None)**

Genera asiento contable para una orden de venta.

**Asiento generado:**
```
Débito:  Cuentas por Cobrar (Activo)   $XXX.XX
Crédito: Ingresos por Ventas (Ingreso)         $XXX.XX
```

**Uso:**
```python
from accounting.utils import create_journal_entry_for_sale
from sales.models import SalesOrder

so = SalesOrder.objects.get(id_sales_order='SO-0001')
journal_entry = create_journal_entry_for_sale(so, request.user)
```

### 3. **create_journal_entry_for_production(work_order, user=None)**

Genera asiento contable para una orden de producción.

**Asiento generado:**
```
Débito:  Inventario Producto Terminado (Activo)  $XXX.XX
Crédito: Inventario Materia Prima (Activo)              $XXX.XX
```

**Uso:**
```python
from accounting.utils import create_journal_entry_for_production
from manufacturing.models import WorkOrder

wo = WorkOrder.objects.get(id_work_order='WO-0001')
journal_entry = create_journal_entry_for_production(wo, request.user)
```

### 4. **create_journal_entry_for_inventory_adjustment(inventory_movement, user=None)**

Genera asiento contable para ajustes de inventario.

**Asiento generado (ajuste positivo):**
```
Débito:  Inventario (Activo)           $XXX.XX
Crédito: Ajustes de Inventario (Ingreso)       $XXX.XX
```

**Asiento generado (ajuste negativo):**
```
Débito:  Ajustes de Inventario (Gasto) $XXX.XX
Crédito: Inventario (Activo)                   $XXX.XX
```

**Uso:**
```python
from accounting.utils import create_journal_entry_for_inventory_adjustment
from inventory.models import InventoryMovement

movement = InventoryMovement.objects.get(id_inventory_movement='IM-0001')
journal_entry = create_journal_entry_for_inventory_adjustment(movement, request.user)
```

### 5. **post_journal_entry(journal_entry_id)**

Contabiliza un asiento (cambia estado a POSTED).

**Uso:**
```python
from accounting.utils import post_journal_entry

posted_entry = post_journal_entry('JE-000001')
```

### 6. **cancel_journal_entry(journal_entry_id)**

Anula un asiento (cambia estado a CANCELLED).

**Uso:**
```python
from accounting.utils import cancel_journal_entry

cancelled_entry = cancel_journal_entry('JE-000001')
```

---

## 🎯 INTEGRACIÓN CON OTROS MÓDULOS

### **Opción 1: Integración Manual**

Puedes llamar las funciones de utilidad desde tus vistas después de crear/confirmar documentos:

```python
# En purchases/views.py
from accounting.utils import create_journal_entry_for_purchase

def confirm_purchase_order(request, order_id):
    po = PurchaseOrder.objects.get(id_purchase_order=order_id)
    # ... lógica de confirmación ...
    
    # Crear asiento contable
    try:
        journal_entry = create_journal_entry_for_purchase(po, request.user)
        messages.success(request, f'Asiento contable {journal_entry.id_journal_entry} creado')
    except Exception as e:
        messages.warning(request, f'Error al crear asiento: {str(e)}')
```

### **Opción 2: Integración con Signals (Recomendado)**

Crea un archivo `accounting/signals.py`:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from purchases.models import PurchaseOrder
from sales.models import SalesOrder
from manufacturing.models import WorkOrder
from .utils import (
    create_journal_entry_for_purchase,
    create_journal_entry_for_sale,
    create_journal_entry_for_production
)

@receiver(post_save, sender=PurchaseOrder)
def create_journal_for_purchase(sender, instance, created, **kwargs):
    """
    Crea asiento contable cuando una orden de compra es recibida
    """
    if instance.status.symbol == 'RECEIVED':
        # Verificar que no exista ya un asiento para esta orden
        from .models import JournalEntry
        exists = JournalEntry.objects.filter(
            reference=instance.id_purchase_order,
            operation_type='PURCHASE'
        ).exists()
        
        if not exists:
            try:
                create_journal_entry_for_purchase(instance)
            except Exception as e:
                print(f"Error creando asiento: {e}")

@receiver(post_save, sender=SalesOrder)
def create_journal_for_sale(sender, instance, created, **kwargs):
    """
    Crea asiento contable cuando una orden de venta es entregada
    """
    if instance.status.symbol == 'DELIVERED':
        from .models import JournalEntry
        exists = JournalEntry.objects.filter(
            reference=instance.id_sales_order,
            operation_type='SALE'
        ).exists()
        
        if not exists:
            try:
                create_journal_entry_for_sale(instance)
            except Exception as e:
                print(f"Error creando asiento: {e}")
```

Registra los signals en `accounting/apps.py`:

```python
from django.apps import AppConfig

class AccountingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounting'

    def ready(self):
        import accounting.signals  # Importar signals
```

---

## 🔐 ADMINISTRACIÓN DJANGO

### **JournalEntryAdmin**

Accede a: `/admin/accounting/journalentry/`

**Características:**
- ✅ Lista con filtros por fecha, tipo de operación, módulo, estado
- ✅ Búsqueda por ID, referencia, descripción
- ✅ Inline de líneas (JournalEntryLine)
- ✅ Indicador visual de balance (✅ Balanceado / ❌ Desbalanceado)
- ✅ Totales de débito y crédito visibles
- ✅ Generación automática de ID al crear nuevo asiento
- ✅ Organización por fieldsets

**Campos de solo lectura:**
- `id_journal_entry` (generado automáticamente)
- `created_at`, `updated_at`, `created_by`
- `get_total_debit`, `get_total_credit`, `is_balanced_display`

### **JournalEntryLineAdmin**

Acceso directo a líneas individuales (opcional, principalmente se usa el inline).

---

## 📊 CONFIGURACIÓN DE CUENTAS CONTABLES

### **IMPORTANTE: Configurar Plan de Cuentas**

Antes de usar el módulo, debes configurar tus cuentas contables en el admin:

#### **Cuentas Requeridas (Ajusta los códigos según tu plan de cuentas):**

1. **Inventario (Activo)**
   - Código: `1.1.05`
   - Naturaleza: Débito
   - Tipo: Activo Corriente

2. **Cuentas por Pagar (Pasivo)**
   - Código: `2.1.01`
   - Naturaleza: Crédito
   - Tipo: Pasivo Corriente

3. **Cuentas por Cobrar (Activo)**
   - Código: `1.1.03`
   - Naturaleza: Débito
   - Tipo: Activo Corriente

4. **Ingresos por Ventas (Ingreso)**
   - Código: `4.1.01`
   - Naturaleza: Crédito
   - Tipo: Ingresos Operacionales

5. **Inventario Producto Terminado (Activo)**
   - Código: `1.1.06`
   - Naturaleza: Débito
   - Tipo: Activo Corriente

6. **Ajustes de Inventario (Gasto/Ingreso)**
   - Código: `5.1.05`
   - Naturaleza: Débito/Crédito
   - Tipo: Gastos Operacionales u Otros Ingresos

### **Cómo crear cuentas:**

1. Ir a `/admin/accounting/accountaccount/`
2. Hacer clic en "Add Account"
3. Completar:
   - **Code**: Código único (ej: 1.1.05)
   - **Name**: Nombre descriptivo (ej: Inventario)
   - **Account Type**: Seleccionar tipo
   - **Account Group**: Seleccionar grupo
   - **Nature**: Seleccionar naturaleza (Débito/Crédito)
   - **Currency**: Seleccionar moneda
   - **Country**: Seleccionar país
   - **Status**: Activo

---

## 🧪 PRUEBAS Y VALIDACIÓN

### **Prueba 1: Crear Asiento Manual desde Admin**

1. Ir a `/admin/accounting/journalentry/add/`
2. Completar:
   - **Date**: Fecha actual
   - **Description**: "Prueba de asiento contable"
   - **Operation Type**: MANUAL
   - **Module**: ACCOUNTING
   - **Reference**: TEST-001
   - **Currency**: Seleccionar moneda
3. Agregar dos líneas:
   - **Línea 1**: Cuenta Débito - $100.00 / Crédito - $0.00
   - **Línea 2**: Cuenta Crédito - $0.00 / Crédito - $100.00
4. Guardar
5. Verificar que aparezca "✅ Balanceado"

### **Prueba 2: Generar Asiento desde Orden de Compra**

```python
# En Django shell
python manage.py shell

from purchases.models import PurchaseOrder
from accounting.utils import create_journal_entry_for_purchase

po = PurchaseOrder.objects.first()
journal_entry = create_journal_entry_for_purchase(po)

print(f"Asiento creado: {journal_entry.id_journal_entry}")
print(f"Total Débito: {journal_entry.get_total_debit()}")
print(f"Total Crédito: {journal_entry.get_total_credit()}")
print(f"Balanceado: {journal_entry.is_balanced()}")
```

### **Prueba 3: Contabilizar Asiento**

```python
from accounting.utils import post_journal_entry

posted = post_journal_entry('JE-000001')
print(f"Estado: {posted.status}")  # Debe mostrar: POSTED
```

---

## 📈 REPORTES CONTABLES (Próxima fase)

Para implementar reportes contables básicos, puedes crear vistas que consulten:

### **Balance de Comprobación**

```python
from accounting.models import JournalEntryLine, AccountAccount
from django.db.models import Sum

def trial_balance():
    accounts = AccountAccount.objects.all()
    results = []
    
    for account in accounts:
        total_debit = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__status='POSTED'
        ).aggregate(Sum('debit'))['debit__sum'] or 0
        
        total_credit = JournalEntryLine.objects.filter(
            account=account,
            journal_entry__status='POSTED'
        ).aggregate(Sum('credit'))['credit__sum'] or 0
        
        balance = total_debit - total_credit
        
        results.append({
            'account': account,
            'debit': total_debit,
            'credit': total_credit,
            'balance': balance
        })
    
    return results
```

### **Libro Mayor por Cuenta**

```python
def general_ledger(account_code, date_from=None, date_to=None):
    account = AccountAccount.objects.get(code=account_code)
    
    lines = JournalEntryLine.objects.filter(
        account=account,
        journal_entry__status='POSTED'
    ).select_related('journal_entry')
    
    if date_from:
        lines = lines.filter(journal_entry__date__gte=date_from)
    if date_to:
        lines = lines.filter(journal_entry__date__lte=date_to)
    
    return lines.order_by('journal_entry__date')
```

---

## ✅ CHECKLIST DE IMPLEMENTACIÓN

- [x] Modelos JournalEntry y JournalEntryLine creados
- [x] Validaciones de balance implementadas
- [x] Generador de ID secuencial implementado
- [x] Admin de Django configurado con inlines
- [x] Utilidades de integración creadas
- [x] Migraciones aplicadas exitosamente
- [x] Documentación completa

### **Pendientes (Opcional):**

- [ ] Crear signals para integración automática
- [ ] Implementar vistas para reportes contables
- [ ] Crear templates para visualización de asientos
- [ ] Implementar exportación a PDF/Excel
- [ ] Agregar permisos por rol para contabilidad
- [ ] Implementar reversión de asientos (crear asiento contrario)
- [ ] Agregar dashboard de contabilidad

---

## 🚀 PRÓXIMOS PASOS RECOMENDADOS

1. **Configurar Plan de Cuentas**
   - Crear cuentas necesarias en admin
   - Validar códigos y naturalezas

2. **Integrar con Módulos Existentes**
   - Agregar llamadas a utilidades en vistas de confirmación
   - O implementar signals para automatización

3. **Probar Flujo Completo**
   - Crear orden de compra → Confirmar → Verificar asiento
   - Crear orden de venta → Entregar → Verificar asiento
   - Crear orden de producción → Completar → Verificar asiento

4. **Implementar Reportes Básicos**
   - Balance de comprobación
   - Libro mayor
   - Estado de resultados

---

## 📞 SOPORTE

Para cualquier duda o problema:
- Revisar logs en `logger` para errores detallados
- Verificar configuración de cuentas contables
- Validar que los módulos origen (purchases, sales, etc.) estén funcionando correctamente
- Asegurar que las monedas estén configuradas

**El módulo de contabilidad está completamente funcional y listo para integración.** 🎉
