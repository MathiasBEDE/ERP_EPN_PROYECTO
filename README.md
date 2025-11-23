# ERP Project – Django ERP Modular System

Sistema ERP modular construido con **Django 5.2.8**, organizado por áreas funcionales del negocio: Compras, Inventario, Ventas, Manufactura, Contabilidad, Proveedores, Materiales, Clientes, Usuarios y Core.

Cada módulo funciona como una app independiente con su propio modelado de datos, panel de administración, formularios y endpoints.

---

##  Características principales

- ✅ **Modelado completo** para Inventario, Compras, Ventas, Manufactura y Contabilidad
- ✅ **Integración automática** entre módulos (Compras → Inventario, Ventas → Inventario, Manufacturing → Inventario)
- ✅ **APIs JSON** para autocompletar proveedores, clientes y materiales
- ✅ **Gestión de estados** en órdenes de compra, venta y trabajo
- ✅ **Movimientos de inventario automáticos** desde recepciones y despachos
- ✅ **Carga masiva CSV** en todos los módulos principales
- ✅ **Sistema de permisos granular** por módulo y usuario
- ✅ **Administración organizada** y profesional
- ✅ **Arquitectura escalable** y mantenible
- ✅ **Protección contra duplicados** en movimientos críticos
- ✅ **Documentación completa** de cada módulo

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
- AccountNature (Naturaleza contable: Débito/Crédito)
- AccountGroup (Grupos de cuentas con prefijos)
- AccountType (Tipos: Activo, Pasivo, Patrimonio, Ingresos, Gastos)
- AccountAccount (Plan de cuentas con jerarquía)

**Características:**
- Sistema de cuentas contables completo
- Jerarquía de cuentas (parent_account)
- Integración con movimientos de inventario
- Generación automática de asientos contables

**Notas:**
- Los modelos **Countries** y **Currency** fueron movidos al módulo `core/`.

**📘 Documentación completa:** Ver [DOCUMENTACION_ACCOUNTING.md](DOCUMENTACION_ACCOUNTING.md)

---

###  CORE

**Datos maestros compartidos en todo el ERP:**

**Modelos incluidos:**
- **Status**: Estados generales del sistema (activo/inactivo)
- **Currency**: Monedas (USD, EUR, etc.) con código y símbolo
- **Country**: Países con código y nombre

**Características:**
- Datos compartidos por todos los módulos
- Gestión centralizada de datos maestros
- Sin duplicación de información

---

###  SUPPLIERS

**Modelo:**
- Supplier (Proveedor)

**Campos principales:**
- ID Supplier (código único)
- Legal Name y Name (razón social y nombre comercial)
- Tax ID (RUC/NIT)
- Ubicación (país, estado, ciudad, dirección, código postal)
- Contacto (teléfono, email, nombre contacto, cargo)
- Información comercial (categoría, términos de pago, moneda, método de pago, cuenta bancaria)
- Estado (activo/inactivo)

**Características:**
- Carga masiva mediante CSV
- Exportación de datos
- 22 campos filtrables
- Integración con módulo de Compras
- API de autocompletado

**📘 Documentación completa:** Ver [DOCUMENTACION_SUPPLIERS.md](DOCUMENTACION_SUPPLIERS.md)

---

###  CUSTOMERS

**Modelo:**
- Customer (Cliente)

**Campos principales:**
- ID Customer (código único)
- Legal Name y Name (razón social y nombre comercial)
- Tax ID (RUC/NIT)
- Ubicación (país, estado, ciudad, dirección, código postal)
- Contacto (teléfono, email, nombre contacto, cargo)
- Información comercial (categoría, términos de pago, moneda, método de pago, cuenta bancaria)
- Estado (activo/inactivo)

**Características:**
- Estructura idéntica a Suppliers pero para clientes
- Carga masiva mediante CSV
- Exportación de datos
- 22 campos filtrables
- Integración con módulo de Ventas

**📘 Documentación completa:** Ver [DOCUMENTACION_CUSTOMERS.md](DOCUMENTACION_CUSTOMERS.md)

---

###  MATERIALS

**Modelos incluidos:**
- Unit (Unidades de medida)
- MaterialType (Tipos de material)
- Material (Materiales/productos)

**Campos del Material:**
- ID Material (código único)
- Nombre
- Descripción
- Unidad de medida
- Tipo de material
- Precio de compra y venta
- Moneda
- Estado (activo/inactivo)

**Características:**
- Gestión completa de materiales y productos
- Carga masiva mediante CSV
- Exportación de datos
- API de autocompletado
- Integración con Compras, Ventas, Inventario y Manufacturing

**📘 Documentación completa:** Ver [DOCUMENTACION_MATERIALS.md](DOCUMENTACION_MATERIALS.md)

---

###  SALES

**Modelos incluidos:**
- SalesOrder (Orden de venta)
- SalesOrderLine (Líneas de orden de venta)

**Campos principales:**
- ID Sales Order (código único)
- Customer (cliente)
- Issue Date (fecha de emisión)
- Status (estado compartido con Purchases)
- Source Location (ubicación de despacho)
- Líneas con material, cantidad, precio unitario y total

**Características:**
- Gestión completa de órdenes de venta
- Integración con Customers
- Integración con Inventory (despachos automáticos)
- Estados compartidos con Purchases
- Cálculo automático de totales
- Movimientos automáticos de inventario al despachar

**📘 Documentación completa:** Ver [DOCUMENTACION_SALES.md](DOCUMENTACION_SALES.md)

---

###  MANUFACTURING

**Modelos incluidos:**
- WorkOrderStatus (Estados de órdenes de trabajo)
- BillOfMaterials (Lista de materiales - BOM)
- BillOfMaterialsLine (Líneas de BOM con componentes)
- WorkOrder (Orden de trabajo de producción)

**Campos principales BOM:**
- ID Bill of Materials (código único)
- Material (producto terminado)
- Líneas con componentes requeridos

**Campos principales Work Order:**
- ID Work Order (código único)
- BOM (lista de materiales)
- Cantidad a producir
- Estado (DRAFT, PLANNED, IN_PROGRESS, COMPLETED, CANCELLED)
- Ubicaciones de origen y destino

**Características:**
- Gestión de listas de materiales (BOM)
- Órdenes de producción
- Consumo automático de componentes
- Generación automática de producto terminado
- Integración con Inventory

**📘 Documentación completa:** Ver [DOCUMENTACION_MANUFACTURING.md](DOCUMENTACION_MANUFACTURING.md)

---

###  REPORTING

**Modelo incluido:**
- ReportSnapshot (Instantáneas de reportes)

**Tipos de reportes:**
- MONTHLY_SUMMARY (Resumen mensual)
- SALES_REPORT (Reporte de ventas)
- PURCHASE_REPORT (Reporte de compras)
- INVENTORY_REPORT (Reporte de inventario)
- PRODUCTION_REPORT (Reporte de producción)
- ACCOUNTING_REPORT (Reporte contable)

**Métricas capturadas:**
- Financieras (ingresos, gastos, utilidad neta)
- Operacionales (ventas, compras, órdenes de producción)
- Valor de inventario
- Datos adicionales en JSON

**Características:**
- Histórico de métricas del ERP
- Comparativas periódicas
- Análisis de tendencias
- Exportación de datos

---

###  USERS

**Modelos incluidos:**
- User (Usuario - extiende AbstractUser)
- Role (Rol con permisos por módulo)
- UserRole (Asignación de roles a usuarios)

**Niveles de permiso:**
- 0: Sin acceso
- 1: Solo visualizar
- 2: Leer y escribir

**Módulos controlados:**
- materials, customers, suppliers, purchases, sales
- inventory, manufacturing, accounting, reporting

**Características:**
- Sistema de autenticación personalizado (AUTH_USER_MODEL)
- Control de permisos granular por módulo
- Múltiples roles por usuario
- Login/Logout con redirección automática
- Context processor para permisos en templates

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

**Core:**
- `/` → Redirige al dashboard o login
- `/dashboard/` → Panel principal con acceso a módulos

**Usuarios:**
- `/login/` → Iniciar sesión
- `/logout/` → Cerrar sesión

**Compras:**
- `/purchases/purchase-order/` → Lista de órdenes de compra
- `/purchases/purchase-order/new/` → Formulario HTML de creación
- `/purchases/purchase-order/<id>/` → Detalle y acciones
- `/purchases/api/supplier/<id>/` → API proveedor  
- `/purchases/api/material/<id>/` → API material  
- `/purchases/api/purchase-order/create/` → Crear pedido (POST JSON)

**Ventas:**
- `/sales/sales-order/` → Lista de órdenes de venta
- `/sales/sales-order/new/` → Crear orden de venta
- `/sales/sales-order/<id>/` → Detalle y acciones

**Inventario:**
- `/inventory/movements/` → Lista de movimientos
- `/inventory/locations/` → Ubicaciones de inventario

**Materiales:**
- `/materials/` → Lista de materiales
- `/materials/create/` → Crear material
- `/materials/<id>/edit/` → Editar material
- `/materials/bulk-upload/` → Carga masiva CSV

**Proveedores:**
- `/suppliers/` → Lista de proveedores
- `/suppliers/create/` → Crear proveedor
- `/suppliers/<id>/edit/` → Editar proveedor
- `/suppliers/bulk-upload/` → Carga masiva CSV

**Clientes:**
- `/customers/` → Lista de clientes
- `/customers/create/` → Crear cliente
- `/customers/<id>/edit/` → Editar cliente
- `/customers/bulk-upload/` → Carga masiva CSV

**Manufacturing:**
- `/manufacturing/work-orders/` → Lista de órdenes de trabajo
- `/manufacturing/bom/` → Listas de materiales (BOM)

**Admin:**
- `/admin/` → Panel de administración Django

---



##  Instalación y ejecución

### 1. Clonar el repositorio

```bash
git clone https://github.com/MathiasBEDE/ERP_EPN_PROYECTO.git
cd ERP_EPN_PROYECTO/erp_project
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv

# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Instalar Django (versión 5.2.8)
pip install django==5.2.8
```

### 3. Configurar base de datos

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Inicializar datos maestros

```bash
# Crear estados de orden de compra
python manage.py init_order_statuses

# Crear tipos de movimiento de inventario
python manage.py init_movement_types

# Verificar/crear ubicación de inventario por defecto
python manage.py init_inventory_location
```

### 5. Crear superusuario

```bash
python manage.py createsuperuser
```

Proporciona:
- Username
- Email
- Password

### 6. Ejecutar servidor de desarrollo

```bash
python manage.py runserver
```

### 7. Acceder a la aplicación

- **Login**: http://127.0.0.1:8000/
- **Dashboard**: http://127.0.0.1:8000/dashboard/
- **Admin**: http://127.0.0.1:8000/admin/

---

##  Configuración inicial desde Admin

Después de ejecutar las migraciones e inicializar datos maestros, accede al panel de administración (`/admin/`) para configurar:

### 1. Core (Datos maestros)
- **Currencies**: Crear monedas (USD, EUR, etc.)
- **Countries**: Crear países necesarios

### 2. Users (Usuarios y permisos)
- **Roles**: Crear roles con permisos por módulo (0=Sin acceso, 1=Ver, 2=Leer/Escribir)
- **User Roles**: Asignar roles a usuarios

### 3. Suppliers (Proveedores)
- **Payment Methods**: Crear métodos de pago (Transferencia, Efectivo, Tarjeta, etc.)

### 4. Materials (Materiales)
- **Units**: Crear unidades de medida (KG, L, UN, etc.)
- **Material Types**: Crear tipos de material (Materia Prima, Producto Terminado, etc.)

### 5. Inventory (Inventario)
- **Movement Types**: Ya creados con comando `init_movement_types`
- **Inventory Locations**: Ya creada ubicación por defecto con comando `init_inventory_location`

### 6. Purchases (Compras)
- **Order Status**: Ya creados con comando `init_order_statuses`

### 7. Manufacturing (Manufactura)
- **Work Order Status**: Crear estados (DRAFT, PLANNED, IN_PROGRESS, COMPLETED, CANCELLED)

### 8. Accounting (Contabilidad)
- **Account Nature**: Crear naturalezas (Débito, Crédito)
- **Account Group**: Crear grupos de cuentas
- **Account Type**: Crear tipos (Activo, Pasivo, Patrimonio, Ingresos, Gastos)
- **Account Account**: Crear plan de cuentas

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

1. **Crear Orden de Compra**:
   - Dashboard → Compras → Nueva Orden
   - Seleccionar proveedor (autocompletado)
   - Agregar líneas con materiales (autocompletado)
   - Estado inicial: DRAFT

2. **Confirmar Orden**:
   - Abrir detalle de la orden
   - Click en "Confirmar Orden"
   - Estado cambia a CONFIRMED

3. **Recibir Orden**:
   - Abrir detalle de la orden confirmada
   - Click en "Recibir Orden"
   - Estado cambia a RECEIVED
   - Se crean automáticamente:
     - Movimientos de inventario (PURCHASE_IN)
     - Actualización de cantidades en stock

4. **Verificar Stock**:
   - Ir a Inventario → Movimientos
   - Ver movimientos automáticos creados
   - Verificar cantidades actualizadas

---

##  Flujo Completo de Ventas

1. **Crear Orden de Venta**:
   - Dashboard → Ventas → Nueva Orden
   - Seleccionar cliente
   - Agregar líneas con materiales/productos
   - Seleccionar ubicación de despacho
   - Estado inicial: DRAFT

2. **Confirmar Orden**:
   - Abrir detalle de la orden
   - Click en "Confirmar Orden"
   - Estado cambia a CONFIRMED

3. **Despachar Orden**:
   - Abrir detalle de la orden confirmada
   - Click en "Despachar Orden"
   - Estado cambia a DISPATCHED
   - Se crean automáticamente:
     - Movimientos de inventario (SALE_OUT)
     - Reducción de stock en ubicación origen

4. **Verificar Stock**:
   - Ir a Inventario → Movimientos
   - Ver movimientos de salida creados
   - Verificar cantidades reducidas

---

##  Flujo Completo de Manufactura

1. **Crear Lista de Materiales (BOM)**:
   - Dashboard → Manufacturing → BOMs → Nuevo
   - Seleccionar producto terminado
   - Agregar componentes requeridos con cantidades

2. **Crear Orden de Trabajo**:
   - Dashboard → Manufacturing → Work Orders → Nueva
   - Seleccionar BOM
   - Indicar cantidad a producir
   - Seleccionar ubicaciones (origen de componentes, destino de producto)
   - Estado inicial: DRAFT

3. **Iniciar Producción**:
   - Abrir detalle de la orden
   - Click en "Iniciar Producción"
   - Estado cambia a IN_PROGRESS
   - Se crean movimientos de salida de componentes

4. **Completar Producción**:
   - Click en "Completar Producción"
   - Estado cambia a COMPLETED
   - Se crean movimientos de entrada de producto terminado
   - Stock actualizado automáticamente

---

##  Gestión de Usuarios y Permisos

1. **Crear Rol**:
   - Admin → Users → Roles → Add
   - Nombre del rol
   - Configurar permisos por módulo (0=Sin acceso, 1=Ver, 2=Leer/Escribir)

2. **Asignar Rol a Usuario**:
   - Admin → Users → User Roles → Add
   - Seleccionar usuario
   - Seleccionar rol
   - Un usuario puede tener múltiples roles

3. **Control de Acceso**:
   - Los permisos se verifican en cada vista
   - Context processor `user_permissions` disponible en todos los templates
   - Ejemplo: `{% if user_permissions.purchases >= 2 %}...{% endif %}`

---

##  Carga Masiva de Datos

Todos los módulos principales soportan carga masiva mediante CSV:

### Materials
```bash
# Descargar plantilla
/materials/bulk-upload/template/

# Formato: delimiter=';'
id_material;name;description;unit;material_type;purchase_price;sale_price;currency;status
```

### Suppliers
```bash
# Descargar plantilla
/suppliers/bulk-upload/template/

# Formato: delimiter=';'
id_supplier;legal_name;name;tax_id;country;state_province;city;address;...
```

### Customers
```bash
# Descargar plantilla
/customers/bulk-upload/template/

# Formato: delimiter=';'
id_customer;legal_name;name;tax_id;country;state_province;city;address;...
```

**Proceso:**
1. Descargar plantilla CSV
2. Llenar datos en Excel/LibreOffice
3. Guardar como CSV con delimiter `;`
4. Subir archivo
5. Sistema valida y reporta errores
6. Registros válidos se crean automáticamente

---

##  Documentación Adicional

Cada módulo cuenta con documentación detallada en archivos individuales:

- **[DOCUMENTACION_MATERIALS.md](DOCUMENTACION_MATERIALS.md)** - Gestión de materiales, unidades y tipos (~1,000 líneas)
- **[DOCUMENTACION_PURCHASES.md](DOCUMENTACION_PURCHASES.md)** - Órdenes de compra, estados y líneas (~1,200 líneas)
- **[DOCUMENTACION_SALES.md](DOCUMENTACION_SALES.md)** - Órdenes de venta y despachos (~1,200 líneas)
- **[DOCUMENTACION_SUPPLIERS.md](DOCUMENTACION_SUPPLIERS.md)** - Gestión de proveedores (~1,300 líneas)
- **[DOCUMENTACION_MANUFACTURING.md](DOCUMENTACION_MANUFACTURING.md)** - BOMs y órdenes de trabajo (~1,400 líneas)
- **[DOCUMENTACION_INVENTORY.md](DOCUMENTACION_INVENTORY.md)** - Movimientos y ubicaciones (~1,600 líneas)
- **[DOCUMENTACION_CUSTOMERS.md](DOCUMENTACION_CUSTOMERS.md)** - Gestión de clientes (~1,300 líneas)
- **[INTEGRATION_PURCHASES_INVENTORY.md](INTEGRATION_PURCHASES_INVENTORY.md)** - Integración Compras → Inventario

---

##  Tecnologías Utilizadas

- **Framework**: Django 5.2.8
- **Base de datos**: SQLite (desarrollo) - PostgreSQL/MySQL (producción)
- **Frontend**: HTML5, CSS (Tailwind CSS), JavaScript
- **Autenticación**: Django Auth con modelo de usuario personalizado
- **Zona horaria**: America/Guayaquil
- **Idioma**: Español (es-es)

---

##  Arquitectura del Proyecto

### Apps Independientes
Cada módulo es una app Django independiente con:
- Modelos propios
- Vistas y URLs
- Templates
- Formularios
- Admin personalizado
- Management commands (donde aplique)

### Integraciones
- **Purchases → Inventory**: Movimientos automáticos al recibir órdenes
- **Sales → Inventory**: Movimientos automáticos al despachar órdenes
- **Manufacturing → Inventory**: Consumo de componentes y generación de productos
- **Accounting**: Integración con todos los módulos para asientos contables
- **Core**: Datos maestros compartidos (monedas, países, estados)

### Base de Datos
- SQLite para desarrollo
- Migraciones automáticas de Django
- Relaciones con PROTECT para integridad referencial
- Campos de auditoría (created_at, updated_at, created_by)

---

##  Comandos de Gestión Disponibles

### Inventario
```bash
# Crear tipos de movimiento
python manage.py init_movement_types

# Crear ubicación por defecto
python manage.py init_inventory_location
```

### Compras
```bash
# Crear estados de orden
python manage.py init_order_statuses
```

---

##  Variables de Configuración (settings.py)

```python
# Autenticación
AUTH_USER_MODEL = 'users.User'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'dashboard'
LOGOUT_REDIRECT_URL = 'login'

# Zona horaria
TIME_ZONE = 'America/Guayaquil'
USE_TZ = True

# Idioma
LANGUAGE_CODE = 'es-es'
USE_I18N = True

# Archivos estáticos
STATIC_URL = 'static/'

# Context processors personalizados
TEMPLATES[0]['OPTIONS']['context_processors'].append(
    'core.context_processors.user_permissions'
)
```

---

##  Estructura de Permisos

### Niveles
- **0**: Sin acceso al módulo
- **1**: Solo visualizar (lectura)
- **2**: Leer y escribir (completo)

### Módulos controlados
- materials
- customers
- suppliers
- purchases
- sales
- inventory
- manufacturing
- accounting
- reporting

### Uso en templates
```html
{% if user_permissions.purchases >= 2 %}
    <!-- Usuario puede crear/editar compras -->
    <a href="{% url 'purchases:create' %}">Nueva Orden</a>
{% elif user_permissions.purchases == 1 %}
    <!-- Usuario solo puede ver -->
    <a href="{% url 'purchases:list' %}">Ver Órdenes</a>
{% endif %}
```

### Uso en views
```python
from core.context_processors import user_permissions

def my_view(request):
    perms = user_permissions(request)
    if perms['user_permissions']['purchases'] < 2:
        return HttpResponseForbidden("No tienes permisos")
    # ... resto del código
```

---

##  Próximas Características

- [ ] Reportes avanzados con gráficos
- [ ] Dashboard con KPIs en tiempo real
- [ ] API REST completa para integraciones externas
- [ ] Notificaciones por email
- [ ] Historial de cambios (audit log)
- [ ] Generación de PDFs para órdenes
- [ ] Integración con sistemas de pago
- [ ] Multi-empresa (tenant)
- [ ] App móvil

---

##  Contribuir

Este proyecto es parte de un sistema ERP académico/empresarial. Para contribuir:

1. Fork del repositorio
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit de cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

---

##  Licencia

Este proyecto es de uso académico/empresarial.

---

**Autor:** Mathias Benavides  
**Versión:** 1.0  
**Última actualización:** Noviembre 17, 2025

