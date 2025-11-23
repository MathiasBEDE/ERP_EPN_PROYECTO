# 🏭 Módulo de Proveedores (Suppliers)

## Descripción General
Módulo encargado de la gestión completa de proveedores, incluyendo información comercial, fiscal, bancaria, contactos y términos de pago. Permite creación individual, edición, eliminación y carga masiva mediante archivos CSV.

---

## Modelos Principales

### 1. **PaymentMethod** (Método de Pago)
Catálogo de métodos de pago disponibles para los proveedores.

**Campos:**
- `name`: Nombre del método - CharField(100, unique=True)
- `symbol`: Símbolo/código - CharField(10, unique=True)

**Métodos:**
- `__str__()`: Retorna formato "Name (Symbol)"
  ```python
  def __str__(self):
      return f"{self.name} ({self.symbol})"
  ```

**Tabla de Base de Datos:** `payment_methods`

**Ejemplos de Registros:**
```
- Transferencia Bancaria (TRANSFER)
- Tarjeta de Crédito (CC)
- Efectivo (CASH)
- Cheque (CHECK)
```

**Índices:**
- `name` (unique, búsqueda rápida)
- `symbol` (unique)

---

### 2. **Supplier** (Proveedor)
Representa un proveedor con toda su información comercial, fiscal y de contacto.

**Campos:**

**Identificación:**
- `id_supplier`: Código único ERP (ej: SUP-001) - CharField(50, unique=True)
- `legal_name`: Razón social legal - CharField(200)
- `name`: Nombre comercial - CharField(200)
- `tax_id`: RUC/NIT/Tax ID - CharField(50)

**Ubicación:**
- `country`: País - CharField(100)
- `state_province`: Provincia/Estado - CharField(100)
- `city`: Ciudad - CharField(100)
- `address`: Dirección completa - CharField(300)
- `zip_code`: Código postal - IntegerField

**Contacto:**
- `phone`: Teléfono - IntegerField
- `email`: Correo electrónico - EmailField
- `contact_name`: Nombre del contacto principal - CharField(200)
- `contact_role`: Cargo del contacto - CharField(100)

**Información Comercial:**
- `category`: Categoría del proveedor - CharField(100)
- `payment_terms`: Términos de pago - CharField(100)
- `currency`: Moneda preferida - CharField(10)
- `payment_method`: Método de pago - ForeignKey(PaymentMethod, PROTECT)
- `bank_account`: Cuenta bancaria - CharField(100)

**Control:**
- `status`: Estado (activo/inactivo) - BooleanField(default=True)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, SET_NULL, null=True)

**Métodos:**

- `__str__()`: Retorna formato "ID - Name"
  ```python
  def __str__(self):
      return f"{self.id_supplier} - {self.name}"
  ```

**Tabla de Base de Datos:** `suppliers`

**Índices:**
- `id_supplier` (unique, búsqueda rápida)
- `-created_at` (proveedores más recientes primero)

**Related Names:**
- `purchase_orders` (desde PurchaseOrder): Órdenes de compra del proveedor

---

## Formularios (Forms)

### 1. **SupplierForm**
Formulario para crear y editar proveedores con validación de Django.

**Campos Incluidos:**
```python
fields = [
    'id_supplier', 'legal_name', 'name', 'tax_id', 'country', 
    'state_province', 'city', 'address', 'zip_code', 'phone', 
    'email', 'contact_name', 'contact_role', 'category', 
    'payment_terms', 'currency', 'payment_method', 'bank_account', 
    'status'
]
```

**Widgets Configurados:**
- TextInput con clases Tailwind CSS
- NumberInput para zip_code y phone
- EmailInput para email
- Select para payment_method

**Placeholders:**
- id_supplier: "SUP-001"
- legal_name: "Razón Social Legal"
- name: "Nombre Comercial"
- tax_id: "RUC/NIT"
- country: "País"
- email: "correo@ejemplo.com"
- etc.

**Validaciones Automáticas:**
- Email válido
- Unicidad de id_supplier
- Campos requeridos según modelo

---

### 2. **CSVUploadForm**
Formulario para carga masiva de proveedores mediante CSV.

**Campos:**
- `csv_file`: FileField con accept=".csv"

**Ayuda:**
- "Upload a CSV file with supplier data. Download the template to see the required format."

**Formato CSV Esperado:**
- Delimitador: `;` (punto y coma)
- Encabezados requeridos: 19 columnas (todos los campos del modelo)

---

## URLs Disponibles

```python
# Vista lista
/suppliers/                           # Lista de proveedores

# CRUD
/suppliers/create/                    # Crear proveedor
/suppliers/<int:id>/edit/            # Editar proveedor
/suppliers/<int:id>/delete/          # Eliminar proveedor

# Carga masiva
/suppliers/bulk-upload/              # Subir CSV
/suppliers/bulk-upload/template/     # Descargar plantilla CSV
```

---

## Vistas (Views)

### 1. **suppliers_list**
Lista paginada de proveedores con filtros avanzados y exportación CSV.

**URL:** `/suppliers/`  
**Método:** GET  
**Decorador:** `@login_required`

**Parámetros GET (Filtros) - 22 filtros disponibles:**

**Identificación:**
- `id_supplier`: Filtrar por código de proveedor (contiene)
- `legal_name`: Filtrar por razón social (contiene)
- `name`: Filtrar por nombre comercial (contiene)
- `tax_id`: Filtrar por RUC/NIT (contiene)

**Ubicación:**
- `country`: Filtrar por país (contiene)
- `state_province`: Filtrar por provincia/estado (contiene)
- `city`: Filtrar por ciudad (contiene)
- `address`: Filtrar por dirección (contiene)
- `zip_code`: Filtrar por código postal (exacto)

**Contacto:**
- `phone`: Filtrar por teléfono (exacto)
- `email`: Filtrar por correo (contiene)
- `contact_name`: Filtrar por nombre de contacto (contiene)
- `contact_role`: Filtrar por cargo de contacto (contiene)

**Comercial:**
- `category`: Filtrar por categoría (contiene)
- `payment_terms`: Filtrar por términos de pago (contiene)
- `currency`: Filtrar por moneda (contiene)
- `payment_method`: Filtrar por ID de método de pago (exacto)
- `bank_account`: Filtrar por cuenta bancaria (contiene)

**Control:**
- `status`: Filtrar por estado ("active" o "inactive")
- `created_at`: Filtrar por fecha de creación (YYYY-MM-DD)
- `updated_at`: Filtrar por fecha de actualización (YYYY-MM-DD)
- `created_by`: Filtrar por usuario creador (username contiene)

**Paginación:**
- `page`: Número de página (10 registros por página)

**Exportación:**
- `export`: Si es "csv", exporta resultados filtrados

**Funcionalidades:**
- ✅ Paginación (10 proveedores por página)
- ✅ 22 filtros combinables
- ✅ Exportación CSV con todos los filtros aplicados
- ✅ Querystring preservado en paginación

**Exportación CSV:**
- Content-Type: `text/csv`
- Filename: `suppliers.csv`
- Separador: coma (,)
- Columnas (22):
  - ID Supplier
  - Legal Name
  - Name
  - Tax ID
  - Country
  - State/Province
  - City
  - Address
  - Zip Code
  - Phone
  - Email
  - Contact Name
  - Contact Role
  - Category
  - Payment Terms
  - Currency
  - Payment Method
  - Bank Account
  - Status (Activo/Inactivo)
  - Created At (DD/MM/YYYY HH:MM)
  - Updated At (DD/MM/YYYY HH:MM)
  - Created By (username o N/A)

**Contexto del Template:**
```python
{
    'page_obj': <Page object con 10 suppliers>,
    'filters': <diccionario con todos los filtros aplicados>,
    'querystring': <querystring para paginación>,
    'payment_methods': <todos los métodos de pago>
}
```

**Ejemplos de uso:**
```
# Todos los proveedores
/suppliers/

# Proveedores activos
/suppliers/?status=active

# Proveedores por país
/suppliers/?country=Ecuador

# Proveedores por ciudad
/suppliers/?city=Quito

# Proveedores por método de pago
/suppliers/?payment_method=1

# Buscar por nombre
/suppliers/?name=acme

# Buscar por email
/suppliers/?email=contact@

# Filtro combinado
/suppliers/?country=Ecuador&status=active&payment_method=1

# Exportar filtrado
/suppliers/?country=Ecuador&export=csv
```

---

### 2. **supplier_create**
Formulario para crear nuevo proveedor.

**URL:** `/suppliers/create/`  
**Métodos:** GET, POST  
**Decorador:** `@login_required`

**Flujo GET:**
1. Crea formulario vacío
2. Renderiza template con formulario

**Flujo POST:**
1. Recibe datos del formulario
2. Valida datos con `SupplierForm`
3. Si es válido:
   - Asigna `created_by = request.user`
   - Guarda en base de datos
   - Redirige a `suppliers:supplier_create` (mismo formulario)
4. Si no es válido:
   - Muestra errores en formulario

**Contexto del Template:**
```python
{
    'form': <SupplierForm instancia>
}
```

**Validaciones:**
- Todos los campos según modelo
- Email válido
- id_supplier único
- Campos numéricos válidos

---

### 3. **supplier_edit**
Formulario para editar proveedor existente.

**URL:** `/suppliers/<int:id>/edit/`  
**Métodos:** GET, POST  
**Parámetro:** `id` es el PK numérico del proveedor  
**Decorador:** `@login_required`

**Flujo GET:**
1. Busca proveedor por ID (404 si no existe)
2. Crea formulario con datos existentes
3. Renderiza template con formulario

**Flujo POST:**
1. Busca proveedor por ID
2. Valida datos actualizados con `SupplierForm`
3. Si es válido:
   - Actualiza campos del proveedor
   - Guarda en base de datos
   - Redirige a `suppliers:suppliers_list`
4. Si no es válido:
   - Muestra errores en formulario

**Contexto del Template:**
```python
{
    'form': <SupplierForm con instancia>,
    'supplier': <Supplier object>,
    'edit_mode': True
}
```

**Validaciones:**
- Proveedor debe existir
- id_supplier único (excepto el actual)
- Todos los campos según modelo

---

### 4. **supplier_delete**
Elimina un proveedor.

**URL:** `/suppliers/<int:id>/delete/`  
**Método:** GET (debería ser POST/DELETE en producción)  
**Parámetro:** `id` es el PK numérico del proveedor  
**Decorador:** `@login_required`

**Proceso:**
1. Busca proveedor por ID (404 si no existe)
2. Elimina el proveedor
3. Redirige a `suppliers:suppliers_list`

**Validaciones:**
- Proveedor debe existir
- Si hay órdenes de compra asociadas, puede fallar (PROTECT)

⚠️ **Advertencia:** Esta vista elimina permanentemente. Considerar usar `status=False` en lugar de eliminar.

---

### 5. **supplier_bulk_upload**
Carga masiva de proveedores mediante archivo CSV.

**URL:** `/suppliers/bulk-upload/`  
**Métodos:** GET, POST  
**Decorador:** `@login_required`

**Control de Permisos:**
- Solo superusuarios o usuarios con role.suppliers ≥ 2
- Sin permisos: Mensaje de error y redirige a lista

**Flujo GET:**
1. Verifica permisos
2. Crea formulario vacío `CSVUploadForm`
3. Renderiza template

**Flujo POST:**

1. **Verifica permisos**

2. **Valida archivo:**
   - Debe ser CSV
   - Tamaño razonable

3. **Decodifica archivo:**
   - Intenta UTF-8 primero
   - Si falla, intenta ISO-8859-1
   - Si ambos fallan: error

4. **Procesa CSV:**
   - Delimitador: `;` (punto y coma)
   - Limpia BOM (Byte Order Mark)
   - Limpia espacios en cabeceras
   - Lee como DictReader

5. **Valida cada fila:**
   ```python
   for row in reader:
       # Limpiar espacios en valores
       cleaned_row = {k.strip(): v.strip() for k, v in row.items()}
       
       # Convertir status a booleano
       status_value = cleaned_row['status'].lower()
       cleaned_row['status'] = status_value in ['true', '1', 'yes', 'active']
       
       # Crear formulario con datos
       supplier_form = SupplierForm(cleaned_row)
       
       if supplier_form.is_valid():
           valid_suppliers.append(supplier)
       else:
           error_rows.append({
               'row': row_number,
               'data': cleaned_row,
               'errors': supplier_form.errors
           })
   ```

6. **Guarda registros válidos:**
   ```python
   if valid_suppliers:
       Supplier.objects.bulk_create(valid_suppliers)
   ```

7. **Genera reporte:**
   - Total de filas procesadas
   - Filas exitosas
   - Filas con errores (con detalle)
   - Mensajes de éxito/advertencia

**Formato CSV Requerido:**

**Delimitador:** `;` (punto y coma)

**Cabeceras (19 columnas):**
```csv
id_supplier;legal_name;name;tax_id;country;state_province;city;address;zip_code;phone;email;contact_name;contact_role;category;payment_terms;currency;payment_method;bank_account;status
```

**Ejemplo de datos:**
```csv
id_supplier;legal_name;name;tax_id;country;state_province;city;address;zip_code;phone;email;contact_name;contact_role;category;payment_terms;currency;payment_method;bank_account;status
SUP-001;ACME Corporation S.A.;ACME Corp;1234567890;Ecuador;Pichincha;Quito;Av. Principal 123;170150;593999999999;contact@acme.com;Juan Pérez;Gerente Comercial;Materia Prima;30 días;USD;1;1234567890123456;true
SUP-002;TechSupply LLC;TechSupply;0987654321;USA;California;San Francisco;Market St 456;94103;14155551234;info@techsupply.com;Mary Johnson;Sales Manager;Equipos;Net 15;USD;1;9876543210987654;active
```

**Valores de status válidos:**
- `true`, `1`, `yes`, `active` → True (activo)
- Cualquier otro valor → False (inactivo)

**Contexto del Template:**
```python
{
    'form': <CSVUploadForm>,
    'upload_complete': True/False,
    'total_rows': <número total>,
    'successful_rows': <número exitosos>,
    'error_count': <número con errores>,
    'error_rows': [
        {
            'row': <número de fila>,
            'data': <datos de la fila>,
            'errors': <errores de validación>
        }
    ]
}
```

**Mensajes:**
- ✅ "Successfully uploaded X suppliers."
- ⚠️ "Y rows had errors and were not uploaded."

---

### 6. **download_template_suppliers**
Descarga plantilla CSV vacía para carga masiva.

**URL:** `/suppliers/bulk-upload/template/`  
**Método:** GET  
**Decorador:** `@login_required`

**Respuesta:**
- Content-Type: `text/csv`
- Filename: `suppliers_template.csv`
- Delimitador: `;` (punto y coma)
- Contenido: Solo cabeceras (19 columnas)

**Cabeceras Incluidas:**
```csv
id_supplier;legal_name;name;tax_id;country;state_province;city;address;zip_code;phone;email;contact_name;contact_role;category;payment_terms;currency;payment_method;bank_account;status
```

**Uso:**
1. Usuario descarga plantilla
2. Llena datos en Excel/LibreOffice
3. Guarda como CSV con delimitador `;`
4. Sube archivo en bulk-upload

---

## Flujo de Trabajo Completo

### 1. Crear Proveedor Individual

**Proceso:**
1. Acceder a `/suppliers/create/`
2. Completar formulario:
   - **Identificación:** ID, razón social, nombre, tax ID
   - **Ubicación:** País, estado, ciudad, dirección, código postal
   - **Contacto:** Teléfono, email, nombre contacto, cargo
   - **Comercial:** Categoría, términos pago, moneda, método pago, cuenta bancaria
   - **Estado:** Activo/Inactivo
3. Click en "Guardar"
4. Sistema valida y guarda
5. Redirige al formulario de creación (listo para agregar otro)

**Ejemplo de datos:**
```
ID: SUP-001
Razón Social: ACME Corporation S.A.
Nombre: ACME Corp
Tax ID: 1234567890001
País: Ecuador
Estado: Pichincha
Ciudad: Quito
Dirección: Av. Principal 123, Edificio Central
Código Postal: 170150
Teléfono: 593999999999
Email: contacto@acme.com
Contacto: Juan Pérez
Cargo: Gerente Comercial
Categoría: Materia Prima
Términos: 30 días
Moneda: USD
Método Pago: Transferencia Bancaria
Cuenta: 1234567890123456
Estado: ✓ Activo
```

---

### 2. Editar Proveedor

**Proceso:**
1. Ir a lista de proveedores: `/suppliers/`
2. Buscar proveedor (con filtros si es necesario)
3. Click en "Editar"
4. Modificar campos necesarios
5. Guardar cambios
6. Redirige a lista de proveedores

**Campos Editables:**
- Todos los campos excepto `created_at` y `created_by`
- id_supplier puede cambiarse (con validación de unicidad)

---

### 3. Desactivar Proveedor

**Opción A: Editar y cambiar status**
1. Editar proveedor
2. Desmarcar checkbox "Status" (o marcarlo como inactivo)
3. Guardar

**Opción B: Eliminar (no recomendado)**
1. Click en "Eliminar" desde lista
2. Proveedor se elimina permanentemente

⚠️ **Recomendación:** Usar status=False en lugar de eliminar para mantener historial.

---

### 4. Carga Masiva de Proveedores

**Proceso Completo:**

**Paso 1: Descargar Plantilla**
1. Ir a `/suppliers/bulk-upload/`
2. Click en "Download Template" o ir a `/suppliers/bulk-upload/template/`
3. Se descarga `suppliers_template.csv`

**Paso 2: Llenar Datos**
1. Abrir plantilla en Excel/LibreOffice
2. Llenar cada columna con datos válidos:
   ```csv
   id_supplier;legal_name;name;tax_id;country;state_province;city;address;zip_code;phone;email;contact_name;contact_role;category;payment_terms;currency;payment_method;bank_account;status
   SUP-001;ACME Corp S.A.;ACME;1234567890;Ecuador;Pichincha;Quito;Av. Principal 123;170150;593999999999;contact@acme.com;Juan Pérez;Gerente;Materia Prima;30 días;USD;1;1234567890123456;true
   SUP-002;Tech LLC;Tech;0987654321;USA;CA;SF;Market St 456;94103;14155551234;info@tech.com;Mary J;Manager;Equipos;Net 15;USD;1;9876543210987654;active
   ```

**Paso 3: Guardar CSV**
- Formato: CSV (delimitado por punto y coma)
- Encoding: UTF-8 o ISO-8859-1
- Delimitador: `;`

**Paso 4: Subir Archivo**
1. Volver a `/suppliers/bulk-upload/`
2. Seleccionar archivo CSV
3. Click en "Upload"
4. Sistema procesa archivo

**Paso 5: Revisar Resultados**
- Ver reporte de carga:
  - Total de filas: 2
  - Exitosas: 2
  - Con errores: 0
- Si hay errores, ver detalle por fila
- Corregir errores y volver a subir

**Ejemplo de Reporte:**
```
✅ Successfully uploaded 5 suppliers.
⚠️ 2 rows had errors and were not uploaded.

Errores encontrados:
- Fila 3: id_supplier: Supplier con este Id supplier ya existe.
- Fila 7: email: Introduzca una dirección de correo electrónico válida.
```

---

### 5. Buscar y Filtrar Proveedores

**Filtros Comunes:**

**Por País:**
```
/suppliers/?country=Ecuador
```

**Por Ciudad:**
```
/suppliers/?city=Quito
```

**Por Estado:**
```
/suppliers/?status=active
```

**Por Categoría:**
```
/suppliers/?category=Materia%20Prima
```

**Por Método de Pago:**
```
/suppliers/?payment_method=1
```

**Búsqueda por Nombre:**
```
/suppliers/?name=acme
```

**Filtros Combinados:**
```
/suppliers/?country=Ecuador&status=active&category=Equipos
```

**Exportar Filtrado:**
```
/suppliers/?country=Ecuador&status=active&export=csv
```

---

## Integraciones con Otros Módulos

### **Purchases (Compras)**
- `PurchaseOrder.supplier`: FK a Supplier
- Validación: Proveedor debe existir (PROTECT)
- No se puede eliminar proveedor con órdenes asociadas

### **Users (Usuarios)**
- `created_by`: Usuario que creó el proveedor
- Control de permisos para bulk upload (role.suppliers ≥ 2)

---

## Reglas de Negocio

### 1. **Código Único**
- `id_supplier` debe ser único en todo el sistema
- Formato recomendado: SUP-XXX
- Sistema no genera automáticamente, debe proporcionarse

### 2. **Datos de Contacto**
- Email debe ser válido (validación Django)
- Teléfono y zip_code deben ser numéricos
- Todos los campos de contacto son obligatorios

### 3. **Método de Pago**
- Debe seleccionarse un método existente
- Valor por defecto: 1 (debe existir en PaymentMethod)
- No se puede eliminar método en uso (PROTECT)

### 4. **Estado del Proveedor**
- `status=True`: Activo (puede usarse en compras)
- `status=False`: Inactivo (no debería usarse)
- Por defecto: True

### 5. **Auditoría**
- `created_at`: Timestamp automático al crear
- `updated_at`: Timestamp automático al actualizar
- `created_by`: Usuario que creó (puede ser null)

### 6. **Integridad Referencial**
- `payment_method`: PROTECT (no se puede eliminar método en uso)
- `created_by`: SET_NULL (si se elimina usuario, se pone null)

---

## Ejemplos de Código

### Crear Proveedor Programáticamente:
```python
from suppliers.models import Supplier, PaymentMethod
from users.models import User

# Obtener método de pago
metodo = PaymentMethod.objects.get(symbol='TRANSFER')

# Crear proveedor
proveedor = Supplier.objects.create(
    id_supplier='SUP-001',
    legal_name='ACME Corporation S.A.',
    name='ACME Corp',
    tax_id='1234567890001',
    country='Ecuador',
    state_province='Pichincha',
    city='Quito',
    address='Av. Principal 123',
    zip_code=170150,
    phone=593999999999,
    email='contacto@acme.com',
    contact_name='Juan Pérez',
    contact_role='Gerente Comercial',
    category='Materia Prima',
    payment_terms='30 días',
    currency='USD',
    payment_method=metodo,
    bank_account='1234567890123456',
    status=True,
    created_by=request.user
)

print(f"Proveedor creado: {proveedor}")
# Output: SUP-001 - ACME Corp
```

---

### Buscar y Filtrar Proveedores:
```python
from suppliers.models import Supplier
from django.db.models import Q

# Todos los proveedores
todos = Supplier.objects.all()

# Proveedores activos
activos = Supplier.objects.filter(status=True)

# Proveedores inactivos
inactivos = Supplier.objects.filter(status=False)

# Por país
ecuador = Supplier.objects.filter(country='Ecuador')

# Por ciudad
quito = Supplier.objects.filter(city='Quito')

# Por categoría
materia_prima = Supplier.objects.filter(category='Materia Prima')

# Por método de pago
transferencia = Supplier.objects.filter(
    payment_method__symbol='TRANSFER'
)

# Búsqueda por nombre (contiene)
busqueda_nombre = Supplier.objects.filter(
    Q(name__icontains='acme') |
    Q(legal_name__icontains='acme')
)

# Búsqueda por email
busqueda_email = Supplier.objects.filter(
    email__icontains='contact@'
)

# Proveedores con términos específicos
pago_30dias = Supplier.objects.filter(
    payment_terms__icontains='30'
)

# Filtro combinado
proveedores_filtrados = Supplier.objects.filter(
    country='Ecuador',
    status=True,
    category='Equipos'
)

# Ordenar por nombre
ordenados = Supplier.objects.all().order_by('name')

# Proveedores más recientes
recientes = Supplier.objects.all().order_by('-created_at')[:10]
```

---

### Actualizar Proveedor:
```python
proveedor = Supplier.objects.get(id_supplier='SUP-001')

# Cambiar dirección
proveedor.address = 'Nueva Avenida 456'
proveedor.city = 'Guayaquil'
proveedor.save()

# Cambiar términos de pago
proveedor.payment_terms = '60 días'
proveedor.save()

# Desactivar proveedor
proveedor.status = False
proveedor.save()

# Actualizar múltiples campos
Supplier.objects.filter(id_supplier='SUP-001').update(
    phone=593988888888,
    email='nuevo@acme.com',
    contact_name='María López'
)
```

---

### Eliminar Proveedor:
```python
# Opción 1: Eliminar permanentemente (no recomendado)
proveedor = Supplier.objects.get(id_supplier='SUP-001')
proveedor.delete()

# Opción 2: Desactivar (recomendado)
proveedor = Supplier.objects.get(id_supplier='SUP-001')
proveedor.status = False
proveedor.save()

# Validar antes de eliminar
from purchases.models import PurchaseOrder

proveedor = Supplier.objects.get(id_supplier='SUP-001')
tiene_ordenes = PurchaseOrder.objects.filter(supplier=proveedor).exists()

if tiene_ordenes:
    print("❌ No se puede eliminar: tiene órdenes asociadas")
    # Desactivar en su lugar
    proveedor.status = False
    proveedor.save()
else:
    proveedor.delete()
```

---

### Carga Masiva Programática:
```python
from suppliers.models import Supplier, PaymentMethod
import csv

# Leer CSV
with open('suppliers.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file, delimiter=';')
    
    proveedores = []
    for row in reader:
        # Convertir status
        status_value = row['status'].lower()
        is_active = status_value in ['true', '1', 'yes', 'active']
        
        # Obtener método de pago
        payment_method = PaymentMethod.objects.get(
            pk=int(row['payment_method'])
        )
        
        # Crear objeto (no guardar aún)
        proveedor = Supplier(
            id_supplier=row['id_supplier'],
            legal_name=row['legal_name'],
            name=row['name'],
            tax_id=row['tax_id'],
            country=row['country'],
            state_province=row['state_province'],
            city=row['city'],
            address=row['address'],
            zip_code=int(row['zip_code']),
            phone=int(row['phone']),
            email=row['email'],
            contact_name=row['contact_name'],
            contact_role=row['contact_role'],
            category=row['category'],
            payment_terms=row['payment_terms'],
            currency=row['currency'],
            payment_method=payment_method,
            bank_account=row['bank_account'],
            status=is_active,
            created_by=request.user
        )
        proveedores.append(proveedor)
    
    # Guardar todos en una operación
    Supplier.objects.bulk_create(proveedores)
    print(f"✅ {len(proveedores)} proveedores creados")
```

---

### Exportar Proveedores a CSV:
```python
import csv
from django.http import HttpResponse
from suppliers.models import Supplier

def exportar_proveedores():
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="suppliers.csv"'
    
    writer = csv.writer(response)
    
    # Encabezados
    writer.writerow([
        'ID', 'Razón Social', 'Nombre', 'Tax ID', 'País', 
        'Estado', 'Ciudad', 'Email', 'Teléfono', 'Categoría', 
        'Términos Pago', 'Moneda', 'Estado'
    ])
    
    # Datos
    proveedores = Supplier.objects.filter(status=True)
    for p in proveedores:
        writer.writerow([
            p.id_supplier,
            p.legal_name,
            p.name,
            p.tax_id,
            p.country,
            p.state_province,
            p.city,
            p.email,
            p.phone,
            p.category,
            p.payment_terms,
            p.currency,
            'Activo' if p.status else 'Inactivo'
        ])
    
    return response
```

---

### Consultas Avanzadas:
```python
from django.db.models import Count, Q
from suppliers.models import Supplier

# Proveedores por país (con conteo)
por_pais = Supplier.objects.values('country').annotate(
    total=Count('id')
).order_by('-total')

for item in por_pais:
    print(f"{item['country']}: {item['total']}")

# Proveedores por categoría
por_categoria = Supplier.objects.values('category').annotate(
    total=Count('id')
).order_by('-total')

# Proveedores por método de pago
por_metodo = Supplier.objects.values(
    'payment_method__name'
).annotate(
    total=Count('id')
).order_by('-total')

# Proveedores con órdenes de compra
from purchases.models import PurchaseOrder

con_ordenes = Supplier.objects.annotate(
    num_ordenes=Count('purchase_orders')
).filter(num_ordenes__gt=0)

# Proveedores sin órdenes
sin_ordenes = Supplier.objects.annotate(
    num_ordenes=Count('purchase_orders')
).filter(num_ordenes=0)

# Top 10 proveedores con más órdenes
top_proveedores = Supplier.objects.annotate(
    num_ordenes=Count('purchase_orders')
).order_by('-num_ordenes')[:10]

for p in top_proveedores:
    print(f"{p.name}: {p.num_ordenes} órdenes")
```

---

## Notas Importantes

### ⚠️ **Advertencias:**

1. **No Eliminar Proveedores con Órdenes:**
   - Genera error PROTECT
   - Pérdida de historial de compras
   - Usar `status=False` en su lugar

2. **Validar IDs Únicos en CSV:**
   - Sistema rechaza duplicados
   - Revisar IDs antes de subir
   - Usar formato consistente (SUP-XXX)

3. **Formato CSV Estricto:**
   - Delimitador debe ser `;` (punto y coma)
   - 19 columnas en orden exacto
   - Status: true/false/1/0/yes/active

4. **Datos Numéricos:**
   - phone y zip_code deben ser números enteros
   - Sin espacios ni guiones
   - Sin prefijo + en teléfonos

5. **Email Válido:**
   - Formato correcto: user@domain.com
   - Sistema valida con Django EmailField
   - Rechaza emails inválidos

6. **Método de Pago:**
   - ID numérico en CSV (ej: 1, 2, 3)
   - Debe existir en PaymentMethod
   - No acepta nombres o símbolos

---

### 💡 **Tips:**

1. **Usar Prefijo Consistente:**
   - SUP-001, SUP-002, etc.
   - Facilita búsqueda y orden
   - Evita conflictos

2. **Completar Todos los Datos:**
   - Más información = mejor gestión
   - Facilita reportes y análisis
   - Evita problemas en compras

3. **Categorizar Proveedores:**
   - Materia Prima
   - Equipos
   - Servicios
   - Logística
   - etc.

4. **Términos de Pago Claros:**
   - "30 días", "60 días", "Contado"
   - "Net 15", "Net 30"
   - Consistencia en formato

5. **Mantener Contactos Actualizados:**
   - Revisar periódicamente
   - Actualizar cuando cambien
   - Múltiples contactos si es necesario

6. **Exportar Regularmente:**
   - Backup de datos
   - Análisis externo
   - Compartir con otros departamentos

---

### 📊 **Mejores Prácticas:**

1. **Desactivar en Lugar de Eliminar:**
   ```python
   # ✅ Bueno
   supplier.status = False
   supplier.save()
   
   # ❌ Evitar
   supplier.delete()
   ```

2. **Validar Antes de Guardar:**
   ```python
   from suppliers.forms import SupplierForm
   
   form = SupplierForm(data)
   if form.is_valid():
       form.save()
   else:
       print(form.errors)
   ```

3. **Usar Transacciones en Bulk:**
   ```python
   from django.db import transaction
   
   with transaction.atomic():
       Supplier.objects.bulk_create(suppliers)
   ```

4. **Filtrar Activos por Defecto:**
   ```python
   # En vistas
   suppliers = Supplier.objects.filter(status=True)
   ```

5. **Logging de Operaciones:**
   ```python
   import logging
   
   logger = logging.getLogger(__name__)
   logger.info(f"Proveedor {supplier.id_supplier} creado por {user}")
   ```

---

### 🔧 **Mantenimiento:**

1. **Limpiar Proveedores Duplicados:**
   ```python
   from django.db.models import Count
   
   duplicados = Supplier.objects.values('tax_id').annotate(
       count=Count('id')
   ).filter(count__gt=1)
   
   for dup in duplicados:
       print(f"Tax ID duplicado: {dup['tax_id']}")
   ```

2. **Actualizar Información Masiva:**
   ```python
   # Cambiar moneda de todos los proveedores de Ecuador
   Supplier.objects.filter(country='Ecuador').update(
       currency='USD'
   )
   ```

3. **Auditoría de Datos:**
   ```python
   # Proveedores sin email
   sin_email = Supplier.objects.filter(
       Q(email__isnull=True) | Q(email='')
   )
   
   # Proveedores sin categoría
   sin_categoria = Supplier.objects.filter(
       Q(category__isnull=True) | Q(category='')
   )
   ```

4. **Verificar Integridad:**
   ```python
   # Proveedores con método de pago inválido
   invalidos = Supplier.objects.exclude(
       payment_method__in=PaymentMethod.objects.all()
   )
   ```

---

## Resumen Técnico

**Modelos:** 2 (Supplier, PaymentMethod)  
**Vistas:** 6 (list, create, edit, delete, bulk_upload, download_template)  
**URLs:** 6  
**Formularios:** 2 (SupplierForm, CSVUploadForm)  
**Paginación:** 10 registros por página  
**Filtros:** 22 campos filtrables  
**Exportación:** CSV con todos los filtros  
**Carga Masiva:** CSV con delimitador `;`  
**Control de Permisos:** Superuser o role.suppliers ≥ 2  

**Campos del Modelo:** 21 campos totales
- Identificación: 4
- Ubicación: 5
- Contacto: 4
- Comercial: 6
- Control: 2

**Integraciones:**
- purchases.PurchaseOrder (FK supplier)
- users.User (FK created_by)

**Validaciones:**
- Email válido
- Campos numéricos
- IDs únicos
- Método de pago existente

**Seguridad:**
- Login requerido en todas las vistas
- Permisos para bulk upload
- PROTECT en FKs críticas
