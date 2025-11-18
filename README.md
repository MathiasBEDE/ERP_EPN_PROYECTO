# ERP Project – Django ERP Modular System

Este proyecto es un ERP modular construido con Django, organizado por áreas funcionales del negocio: Compras, Inventario, Contabilidad, Proveedores, Materiales, Clientes, Usuarios y Core.
Cada módulo funciona como una app independiente con su propio modelado de datos, panel de administración y endpoints.

Actualmente el proyecto cuenta con:

Modelado de datos completo para Inventario, Compras y Contabilidad

APIs internas para autocompletado y validación

Formularios funcionales

Administración mejorada

Separación clara por apps
#  ERP JM – Django Modular ERP System

ERP JM es un ERP modular construido con **Django**, organizado por áreas funcionales reales:  
**Compras, Inventario, Contabilidad, Materiales, Proveedores y Core**.

Cada módulo funciona como una app independiente con su propio **modelado de datos**,  
**panel de administración** y **endpoints internos**.

---

##  Características principales

- Modelado completo para **Inventario**, **Compras** y **Contabilidad**
- **APIs JSON** para autocompletar proveedores y materiales
- Formulario funcional para **crear pedidos de compra**
- Administración organizada, limpia y profesional
- Separación clara por módulos (arquitectura escalable)
- Código mantenible y organizado por dominios empresariales

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

**Incluye:**
- Formularios bien estructurados  
- Campos del sistema ocultos en el admin  
- Opciones de búsqueda y filtros en Django admin  

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
- OrderStatus  
- PurchaseOrder  
- PurchaseOrderLine  

**APIs implementadas:**
- `/purchases/api/supplier/<id>/` → Datos del proveedor  
- `/purchases/api/material/<id>/` → Datos del material  
- `/purchases/api/purchase-order/create/` → Crear pedido vía JSON  

**Formulario HTML de creación de pedido:**

El formulario:
- Autocompleta datos del proveedor  
- Autocompleta material, unidad y moneda  
- Permite agregar y eliminar líneas dinámicas  

---

##  URLs principales

/purchases/purchase-order/new/            → Formulario HTML  
/purchases/api/supplier/<id>/            → API proveedor  
/purchases/api/material/<id>/            → API material  
/purchases/api/purchase-order/create/    → Crear pedido (POST JSON)  

---



##  Instalación y ejecución

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
**Autor Mathias Benavides**

