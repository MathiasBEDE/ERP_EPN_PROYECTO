# ERP Project – Django ERP Modular System

Este proyecto es un ERP modular construido con Django, organizado por áreas funcionales del negocio: Compras, Inventario, Contabilidad, Proveedores, Materiales, Clientes, Usuarios y Core.
Cada módulo funciona como una app independiente con su propio modelado de datos, panel de administración y endpoints.

Actualmente el proyecto cuenta con:

Modelado de datos completo para Inventario, Compras y Contabilidad

APIs internas para autocompletado y validación

Formularios funcionales

Administración mejorada

Separación clara por apps
#  ERP – Django Modular ERP System

ERP JM es un ERP modular construido con **Django**, organizado por áreas funcionales reales:  
**Compras, Inventario, Contabilidad, Materiales, Proveedores y Core**.

Cada módulo funciona como una app independiente con su propio **modelado de datos**,  
**panel de administración** y **endpoints internos**.

---

##  Características principales

- Modelado completo para **Inventario**, **Compras** y **Contabilidad**
- **Integración Compras → Inventario**: Actualización automática de stock al recibir órdenes
- **APIs JSON** para autocompletar proveedores y materiales
- Formulario funcional para **crear pedidos de compra** con líneas dinámicas
- **Gestión de estados** de órdenes de compra (Draft, Confirmed, Received, Cancelled, Closed, Invoiced)
- **Movimientos de inventario** automáticos desde recepciones de compras
- Administración organizada, limpia y profesional
- Separación clara por módulos (arquitectura escalable)
- Código mantenible y organizado por dominios empresariales
- **Protección contra duplicados** en movimientos de inventario

---

##  Estructura del proyecto
```
ERP_PROJECT/
│
├── accounting/               # Naturaleza contable, grupos, tipos y cuentas contables
│
├── core/                     # Países, Monedas, Estados (Statuses)
│
├── customers/
│
├── inventory/                # Localizaciones, tipos de movimiento, movimientos
│
├── materials/                # Materiales, unidades, tipos, monedas
│
├── purchases/                # Pedidos de compra, líneas y APIs
│   ├── views.py              # APIs + formulario de creación de pedido
│   ├── urls.py               # Rutas del módulo de compras
│   └── models.py             # PurchaseOrder, PurchaseOrderLine, OrderStatus
│
├── suppliers/                # Proveedores del sistema
│
├── users/
│
├── erp_project/              # Configuración principal del proyecto
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
└── db.sqlite3
```
---

##  Módulos Implementados

###  INVENTORY

**Modelos incluidos:**
- MovementType  
- InventoryLocation  
- InventoryMovement  

**Características:**
- Formularios bien estructurados  
- Campos del sistema ocultos en el admin  
- Opciones de búsqueda y filtros en Django admin  
- **Integración con Compras**: Movimientos automáticos al recibir órdenes
- Campos `movement_date` y `reference` para trazabilidad
- Función utilitaria `get_default_inventory_location()`

**Tipos de Movimiento:**
- PURCHASE_IN (Entrada por Compra)
- SALE_OUT (Salida por Venta)
- ADJUSTMENT_IN/OUT (Ajustes)
- TRANSFER_IN/OUT (Transferencias)

---

###  ACCOUNTING

**Modelos incluidos:**
- AccountNature  
- AccountGroup  
- AccountType  
- AccountAccount  

**Notas:**
- Los modelos **Countries** y **Currency** fueron movidos al módulo `core/`.

---

###  CORE

**Datos maestros compartidos en todo el ERP:**
- Countries  
- Currencies  
- Statuses  

---

###  SUPPLIERS

**Información del proveedor:**
- ID Supplier  
- Nombre  
- Dirección  
- Ciudad  
- Estado / Provincia  
- País  

Esta información se autocompleta mediante API en el módulo de Compras.

---

###  MATERIALS

**Información usada en las líneas del pedido:**
- ID Material  
- Nombre  
- Unidad  
- Moneda  
- Tipo de material  

---

###  PURCHASES

**Modelos:**
- OrderStatus (DRAFT, CONFIRMED, RECEIVED, CANCELLED, CLOSED, INVOICED)
- PurchaseOrder  
- PurchaseOrderLine  

**APIs implementadas:**
- `/purchases/api/supplier/<id>/` → Datos del proveedor  
- `/purchases/api/material/<id>/` → Datos del material  
- `/purchases/api/purchase-order/create/` → Crear pedido vía JSON  

**Vistas implementadas:**
- `/purchases/purchase-order/` → Lista de órdenes con filtros
- `/purchases/purchase-order/new/` → Formulario de creación
- `/purchases/purchase-order/<id>/` → Detalle y acciones (Recibir, Cancelar, Cerrar)

**Formulario HTML de creación de pedido:**

El formulario:
- Autocompleta datos del proveedor  
- Autocompleta material, unidad y moneda  
- Permite agregar y eliminar líneas dinámicas
- Usa delegación de eventos para líneas ilimitadas

**Integración con Inventario:**
- Al marcar una orden como "Fully Received" (RECEIVED):
  - Se actualizan automáticamente las cantidades recibidas
  - Se crean movimientos de inventario tipo PURCHASE_IN
  - Se registra la referencia a la orden en cada movimiento
  - Todo el proceso es atómico (transacción completa o rollback)
  - Protección contra movimientos duplicados

**📘 Documentación completa:** Ver [INTEGRATION_PURCHASES_INVENTORY.md](INTEGRATION_PURCHASES_INVENTORY.md)

---

##  URLs principales

**Compras:**
- `/purchases/purchase-order/` → Lista de órdenes
- `/purchases/purchase-order/new/` → Formulario HTML de creación
- `/purchases/purchase-order/<id>/` → Detalle y acciones
- `/purchases/api/supplier/<id>/` → API proveedor  
- `/purchases/api/material/<id>/` → API material  
- `/purchases/api/purchase-order/create/` → Crear pedido (POST JSON)

**Dashboard:**
- `/dashboard/` → Panel principal con acceso a módulos

**Admin:**
- `/admin/` → Panel de administración Django

---



##  Instalación y ejecución

### 1. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar base de datos

```bash
python manage.py makemigrations
python manage.py migrate
```

### 3. Inicializar datos maestros

```bash
# Crear estados de orden de compra
python manage.py init_order_statuses

# Crear tipos de movimiento de inventario
python manage.py init_movement_types

# Verificar/crear ubicación de inventario por defecto
python manage.py init_inventory_location
```

### 4. Crear superusuario

```bash
python manage.py createsuperuser
```

### 5. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

### 6. Acceder a la aplicación

- **Dashboard**: http://127.0.0.1:8000/dashboard/
- **Admin**: http://127.0.0.1:8000/admin/

---

##  Pruebas

### Prueba de Integración Compras → Inventario

```bash
python test_purchase_inventory_integration.py
```

Este script verifica:
- ✓ Creación de órdenes de compra
- ✓ Cambio de estado a RECEIVED
- ✓ Creación automática de movimientos de inventario
- ✓ Protección contra duplicados
- ✓ Integridad de referencias

---

##  Flujo Completo de Compras

1. **Crear Orden**: Dashboard → Compras → Nueva Orden
2. **Agregar Líneas**: Usar autocompletado para materiales
3. **Guardar**: Estado inicial = DRAFT
4. **Recibir**: Abrir detalle → Click "Recibir Orden"
5. **Verificar**: Stock actualizado en Inventario

---

##  Documentación Adicional

- [Integración Compras → Inventario](INTEGRATION_PURCHASES_INVENTORY.md) - Documentación completa de la integración
- [Django Admin](http://127.0.0.1:8000/admin/) - Panel de administración
- [API Endpoints](http://127.0.0.1:8000/purchases/api/) - Documentación de APIs

---

**Autor:** Mathias Benavides  
**Versión:** 1.0  
**Última actualización:** Noviembre 17, 2025

