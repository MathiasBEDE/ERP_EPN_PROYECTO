# 👥 Módulo de Clientes (Customers)

## Descripción General
Módulo encargado de la gestión completa de clientes, incluyendo información comercial, fiscal, bancaria, contactos y términos de pago. Permite creación individual, edición, eliminación y carga masiva mediante archivos CSV. Estructura idéntica al módulo de proveedores pero orientado a clientes.

---

## Modelos Principales

### **Customer** (Cliente)
Representa un cliente con toda su información comercial, fiscal y de contacto.

**Campos:**

**Identificación:**
- `id_customer`: Código único ERP (ej: CUST-001) - CharField(50, unique=True)
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
- `category`: Categoría del cliente - CharField(100)
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
      return f"{self.id_customer} - {self.name}"
  ```

**Tabla de Base de Datos:** `customers`

**Índices:**
- `id_customer` (unique, búsqueda rápida)
- `-created_at` (clientes más recientes primero)

**Related Names:**
- `sales_orders` (desde SalesOrder): Órdenes de venta del cliente

---

## Formularios (Forms)

### 1. **CustomerForm**
Formulario para crear y editar clientes con validación de Django.

**Campos Incluidos:**
```python
fields = [
    'id_customer', 'legal_name', 'name', 'tax_id', 'country', 
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
- id_customer: "CUS-001"
- legal_name: "Razón Social Legal"
- name: "Nombre Comercial"
- tax_id: "RUC/NIT"
- country: "País"
- email: "correo@ejemplo.com"
- etc.

**Validaciones Automáticas:**
- Email válido
- Unicidad de id_customer
- Campos requeridos según modelo

---

### 2. **CSVUploadForm**
Formulario para carga masiva de clientes mediante CSV.

**Campos:**
- `csv_file`: FileField con accept=".csv"

**Ayuda:**
- "Upload a CSV file with customer data. Download the template to see the required format."

**Formato CSV Esperado:**
- Delimitador: `;` (punto y coma)
- Encabezados requeridos: 19 columnas (todos los campos del modelo)

---

## URLs Disponibles

```python
# Vista lista
/customers/                           # Lista de clientes

# CRUD
/customers/create/                    # Crear cliente
/customers/<int:id>/edit/            # Editar cliente
/customers/<int:id>/delete/          # Eliminar cliente

# Carga masiva
/customers/bulk-upload/              # Subir CSV
/customers/bulk-upload/template/     # Descargar plantilla CSV
```

---

## Vistas (Views)

### 1. **customers_list**
Lista paginada de clientes con filtros avanzados y exportación CSV.

**URL:** `/customers/`  
**Método:** GET  
**Decorador:** `@login_required`

**Parámetros GET (Filtros) - 22 filtros disponibles:**

**Identificación:**
- `id_customer`: Filtrar por código de cliente (contiene)
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
- ✅ Paginación (10 clientes por página)
- ✅ 22 filtros combinables
- ✅ Exportación CSV con todos los filtros aplicados
- ✅ Querystring preservado en paginación

**Exportación CSV:**
- Content-Type: `text/csv`
- Filename: `customers.csv`
- Separador: punto y coma (;)
- Columnas (22):
  - ID Customer
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
    'page_obj': <Page object con 10 customers>,
    'filters': <diccionario con todos los filtros aplicados>,
    'querystring': <querystring para paginación>,
    'payment_methods': <todos los métodos de pago>
}
```

**Ejemplos de uso:**
```
# Todos los clientes
/customers/

# Clientes activos
/customers/?status=active

# Clientes por país
/customers/?country=Ecuador

# Clientes por ciudad
/customers/?city=Quito

# Clientes por método de pago
/customers/?payment_method=1

# Buscar por nombre
/customers/?name=acme

# Buscar por email
/customers/?email=contact@

# Filtro combinado
/customers/?country=Ecuador&status=active&payment_method=1

# Exportar filtrado
/customers/?country=Ecuador&export=csv
```

---

### 2. **customer_create**
Formulario para crear nuevo cliente.

**URL:** `/customers/create/`  
**Métodos:** GET, POST  
**Decorador:** `@login_required`

**Flujo GET:**
1. Crea formulario vacío
2. Renderiza template con formulario

**Flujo POST:**
1. Recibe datos del formulario
2. Valida datos con `CustomerForm`
3. Si es válido:
   - Asigna `created_by = request.user`
   - Guarda en base de datos
   - Redirige a `customers:customer_create` (mismo formulario)
4. Si no es válido:
   - Muestra errores en formulario

**Contexto del Template:**
```python
{
    'form': <CustomerForm instancia>
}
```

**Validaciones:**
- Todos los campos según modelo
- Email válido
- id_customer único
- Campos numéricos válidos

---

### 3. **customer_edit**
Formulario para editar cliente existente.

**URL:** `/customers/<int:id>/edit/`  
**Métodos:** GET, POST  
**Parámetro:** `id` es el PK numérico del cliente  
**Decorador:** `@login_required`

**Flujo GET:**
1. Busca cliente por ID (404 si no existe)
2. Crea formulario con datos existentes
3. Renderiza template con formulario

**Flujo POST:**
1. Busca cliente por ID
2. Valida datos actualizados con `CustomerForm`
3. Si es válido:
   - Actualiza campos del cliente
   - Guarda en base de datos
   - Redirige a `customers:customers_list`
4. Si no es válido:
   - Muestra errores en formulario

**Contexto del Template:**
```python
{
    'form': <CustomerForm con instancia>,
    'customer': <Customer object>,
    'edit_mode': True
}
```

**Validaciones:**
- Cliente debe existir
- id_customer único (excepto el actual)
- Todos los campos según modelo

---

### 4. **customer_delete**
Elimina un cliente.

**URL:** `/customers/<int:id>/delete/`  
**Método:** GET (debería ser POST/DELETE en producción)  
**Parámetro:** `id` es el PK numérico del cliente  
**Decorador:** `@login_required`

**Proceso:**
1. Busca cliente por ID (404 si no existe)
2. Elimina el cliente
3. Redirige a `customers:customers_list`

**Validaciones:**
- Cliente debe existir
- Si hay órdenes de venta asociadas, puede fallar (PROTECT)

⚠️ **Advertencia:** Esta vista elimina permanentemente. Considerar usar `status=False` en lugar de eliminar.

---

### 5. **customer_bulk_upload**
Carga masiva de clientes mediante archivo CSV.

**URL:** `/customers/bulk-upload/`  
**Métodos:** GET, POST  
**Decorador:** `@login_required`

**Control de Permisos:**
- Solo superusuarios o usuarios con role.customers ≥ 2
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
       customer_form = CustomerForm(cleaned_row)
       
       if customer_form.is_valid():
           valid_customers.append(customer)
       else:
           error_rows.append({
               'row': row_number,
               'data': cleaned_row,
               'errors': customer_form.errors
           })
   ```

6. **Guarda registros válidos:**
   ```python
   if valid_customers:
       Customer.objects.bulk_create(valid_customers)
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
id_customer;legal_name;name;tax_id;country;state_province;city;address;zip_code;phone;email;contact_name;contact_role;category;payment_terms;currency;payment_method;bank_account;status
```

**Ejemplo de datos:**
```csv
id_customer;legal_name;name;tax_id;country;state_province;city;address;zip_code;phone;email;contact_name;contact_role;category;payment_terms;currency;payment_method;bank_account;status
CUST-001;Tech Solutions S.A.;Tech Solutions;1234567890;Ecuador;Pichincha;Quito;Av. Amazonas 123;170150;593999999999;contact@tech.com;Juan Pérez;Gerente Compras;Tecnología;30 días;USD;1;1234567890123456;true
CUST-002;Retail Corp LLC;Retail Corp;0987654321;USA;Texas;Houston;Main St 456;77002;14135551234;info@retail.com;Mary Johnson;Purchasing Manager;Retail;Net 15;USD;1;9876543210987654;active
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
- ✅ "Successfully uploaded X customers."
- ⚠️ "Y rows had errors and were not uploaded."

---

### 6. **download_template_customers**
Descarga plantilla CSV vacía para carga masiva.

**URL:** `/customers/bulk-upload/template/`  
**Método:** GET  
**Decorador:** `@login_required`

**Respuesta:**
- Content-Type: `text/csv`
- Filename: `customers_template.csv`
- Delimitador: `;` (punto y coma)
- Contenido: Solo cabeceras (19 columnas)

**Cabeceras Incluidas:**
```csv
id_customer;legal_name;name;tax_id;country;state_province;city;address;zip_code;phone;email;contact_name;contact_role;category;payment_terms;currency;payment_method;bank_account;status
```

**Uso:**
1. Usuario descarga plantilla
2. Llena datos en Excel/LibreOffice
3. Guarda como CSV con delimitador `;`
4. Sube archivo en bulk-upload

---

## Flujo de Trabajo Completo

### 1. Crear Cliente Individual

**Proceso:**
1. Acceder a `/customers/create/`
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
ID: CUST-001
Razón Social: Tech Solutions S.A.
Nombre: Tech Solutions
Tax ID: 1234567890001
País: Ecuador
Estado: Pichincha
Ciudad: Quito
Dirección: Av. Amazonas 123, Edificio Tech Tower
Código Postal: 170150
Teléfono: 593999999999
Email: contacto@tech.com
Contacto: Juan Pérez
Cargo: Gerente de Compras
Categoría: Tecnología
Términos: 30 días
Moneda: USD
Método Pago: Transferencia Bancaria
Cuenta: 1234567890123456
Estado: ✓ Activo
```

---

### 2. Editar Cliente

**Proceso:**
1. Ir a lista de clientes: `/customers/`
2. Buscar cliente (con filtros si es necesario)
3. Click en "Editar"
4. Modificar campos necesarios
5. Guardar cambios
6. Redirige a lista de clientes

**Campos Editables:**
- Todos los campos excepto `created_at` y `created_by`
- id_customer puede cambiarse (con validación de unicidad)

---

### 3. Desactivar Cliente

**Opción A: Editar y cambiar status**
1. Editar cliente
2. Desmarcar checkbox "Status" (o marcarlo como inactivo)
3. Guardar

**Opción B: Eliminar (no recomendado)**
1. Click en "Eliminar" desde lista
2. Cliente se elimina permanentemente

⚠️ **Recomendación:** Usar status=False en lugar de eliminar para mantener historial.

---

### 4. Carga Masiva de Clientes

**Proceso Completo:**

**Paso 1: Descargar Plantilla**
1. Ir a `/customers/bulk-upload/`
2. Click en "Download Template" o ir a `/customers/bulk-upload/template/`
3. Se descarga `customers_template.csv`

**Paso 2: Llenar Datos**
1. Abrir plantilla en Excel/LibreOffice
2. Llenar cada columna con datos válidos:
   ```csv
   id_customer;legal_name;name;tax_id;country;state_province;city;address;zip_code;phone;email;contact_name;contact_role;category;payment_terms;currency;payment_method;bank_account;status
   CUST-001;Tech Solutions S.A.;Tech Solutions;1234567890;Ecuador;Pichincha;Quito;Av. Amazonas 123;170150;593999999999;contact@tech.com;Juan Pérez;Gerente;Tecnología;30 días;USD;1;1234567890123456;true
   CUST-002;Retail Corp;Retail;0987654321;USA;TX;Houston;Main St 456;77002;14135551234;info@retail.com;Mary J;Manager;Retail;Net 15;USD;1;9876543210987654;active
   ```

**Paso 3: Guardar CSV**
- Formato: CSV (delimitado por punto y coma)
- Encoding: UTF-8 o ISO-8859-1
- Delimitador: `;`

**Paso 4: Subir Archivo**
1. Volver a `/customers/bulk-upload/`
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
✅ Successfully uploaded 5 customers.
⚠️ 2 rows had errors and were not uploaded.

Errores encontrados:
- Fila 3: id_customer: Customer con este Id customer ya existe.
- Fila 7: email: Introduzca una dirección de correo electrónico válida.
```

---

### 5. Buscar y Filtrar Clientes

**Filtros Comunes:**

**Por País:**
```
/customers/?country=Ecuador
```

**Por Ciudad:**
```
/customers/?city=Quito
```

**Por Estado:**
```
/customers/?status=active
```

**Por Categoría:**
```
/customers/?category=Tecnología
```

**Por Método de Pago:**
```
/customers/?payment_method=1
```

**Búsqueda por Nombre:**
```
/customers/?name=tech
```

**Filtros Combinados:**
```
/customers/?country=Ecuador&status=active&category=Tecnología
```

**Exportar Filtrado:**
```
/customers/?country=Ecuador&status=active&export=csv
```

---

## Integraciones con Otros Módulos

### **Sales (Ventas)**
- `SalesOrder.customer`: FK a Customer
- Validación: Cliente debe existir y estar activo (status=True)
- No se puede eliminar cliente con órdenes asociadas (PROTECT)

### **Users (Usuarios)**
- `created_by`: Usuario que creó el cliente
- Control de permisos para bulk upload (role.customers ≥ 2)

### **Suppliers (Proveedores)**
- Comparte modelo `PaymentMethod`
- Misma estructura pero entidades diferentes

---

## Reglas de Negocio

### 1. **Código Único**
- `id_customer` debe ser único en todo el sistema
- Formato recomendado: CUST-XXX o CUS-XXX
- Sistema no genera automáticamente, debe proporcionarse

### 2. **Datos de Contacto**
- Email debe ser válido (validación Django)
- Teléfono y zip_code deben ser numéricos
- Todos los campos de contacto son obligatorios

### 3. **Método de Pago**
- Debe seleccionarse un método existente
- Valor por defecto: 1 (debe existir en PaymentMethod)
- No se puede eliminar método en uso (PROTECT)

### 4. **Estado del Cliente**
- `status=True`: Activo (puede usarse en ventas)
- `status=False`: Inactivo (no debería usarse)
- Por defecto: True

### 5. **Auditoría**
- `created_at`: Timestamp automático al crear
- `updated_at`: Timestamp automático al actualizar
- `created_by`: Usuario que creó (puede ser null)

### 6. **Integridad Referencial**
- `payment_method`: PROTECT (no se puede eliminar método en uso)
- `created_by`: SET_NULL (si se elimina usuario, se pone null)
- Cliente con SalesOrders: PROTECT (no se puede eliminar)

---

## Ejemplos de Código

### Crear Cliente Programáticamente:
```python
from customers.models import Customer
from suppliers.models import PaymentMethod
from users.models import User

# Obtener método de pago
metodo = PaymentMethod.objects.get(symbol='TRANSFER')

# Crear cliente
cliente = Customer.objects.create(
    id_customer='CUST-001',
    legal_name='Tech Solutions S.A.',
    name='Tech Solutions',
    tax_id='1234567890001',
    country='Ecuador',
    state_province='Pichincha',
    city='Quito',
    address='Av. Amazonas 123',
    zip_code=170150,
    phone=593999999999,
    email='contacto@tech.com',
    contact_name='Juan Pérez',
    contact_role='Gerente de Compras',
    category='Tecnología',
    payment_terms='30 días',
    currency='USD',
    payment_method=metodo,
    bank_account='1234567890123456',
    status=True,
    created_by=request.user
)

print(f"Cliente creado: {cliente}")
# Output: CUST-001 - Tech Solutions
```

---

### Buscar y Filtrar Clientes:
```python
from customers.models import Customer
from django.db.models import Q

# Todos los clientes
todos = Customer.objects.all()

# Clientes activos
activos = Customer.objects.filter(status=True)

# Clientes inactivos
inactivos = Customer.objects.filter(status=False)

# Por país
ecuador = Customer.objects.filter(country='Ecuador')

# Por ciudad
quito = Customer.objects.filter(city='Quito')

# Por categoría
tecnologia = Customer.objects.filter(category='Tecnología')

# Por método de pago
transferencia = Customer.objects.filter(
    payment_method__symbol='TRANSFER'
)

# Búsqueda por nombre (contiene)
busqueda_nombre = Customer.objects.filter(
    Q(name__icontains='tech') |
    Q(legal_name__icontains='tech')
)

# Búsqueda por email
busqueda_email = Customer.objects.filter(
    email__icontains='contact@'
)

# Clientes con términos específicos
pago_30dias = Customer.objects.filter(
    payment_terms__icontains='30'
)

# Filtro combinado
clientes_filtrados = Customer.objects.filter(
    country='Ecuador',
    status=True,
    category='Tecnología'
)

# Ordenar por nombre
ordenados = Customer.objects.all().order_by('name')

# Clientes más recientes
recientes = Customer.objects.all().order_by('-created_at')[:10]
```

---

### Actualizar Cliente:
```python
cliente = Customer.objects.get(id_customer='CUST-001')

# Cambiar dirección
cliente.address = 'Nueva Avenida 456'
cliente.city = 'Guayaquil'
cliente.save()

# Cambiar términos de pago
cliente.payment_terms = '60 días'
cliente.save()

# Desactivar cliente
cliente.status = False
cliente.save()

# Actualizar múltiples campos
Customer.objects.filter(id_customer='CUST-001').update(
    phone=593988888888,
    email='nuevo@tech.com',
    contact_name='María López'
)
```

---

### Eliminar Cliente:
```python
# Opción 1: Eliminar permanentemente (no recomendado)
cliente = Customer.objects.get(id_customer='CUST-001')
cliente.delete()

# Opción 2: Desactivar (recomendado)
cliente = Customer.objects.get(id_customer='CUST-001')
cliente.status = False
cliente.save()

# Validar antes de eliminar
from sales.models import SalesOrder

cliente = Customer.objects.get(id_customer='CUST-001')
tiene_ordenes = SalesOrder.objects.filter(customer=cliente).exists()

if tiene_ordenes:
    print("❌ No se puede eliminar: tiene órdenes asociadas")
    # Desactivar en su lugar
    cliente.status = False
    cliente.save()
else:
    cliente.delete()
```

---

### Carga Masiva Programática:
```python
from customers.models import Customer
from suppliers.models import PaymentMethod
import csv

# Leer CSV
with open('customers.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file, delimiter=';')
    
    clientes = []
    for row in reader:
        # Convertir status
        status_value = row['status'].lower()
        is_active = status_value in ['true', '1', 'yes', 'active']
        
        # Obtener método de pago
        payment_method = PaymentMethod.objects.get(
            pk=int(row['payment_method'])
        )
        
        # Crear objeto (no guardar aún)
        cliente = Customer(
            id_customer=row['id_customer'],
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
        clientes.append(cliente)
    
    # Guardar todos en una operación
    Customer.objects.bulk_create(clientes)
    print(f"✅ {len(clientes)} clientes creados")
```

---

### Exportar Clientes a CSV:
```python
import csv
from django.http import HttpResponse
from customers.models import Customer

def exportar_clientes():
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers.csv"'
    
    writer = csv.writer(response)
    
    # Encabezados
    writer.writerow([
        'ID', 'Razón Social', 'Nombre', 'Tax ID', 'País', 
        'Estado', 'Ciudad', 'Email', 'Teléfono', 'Categoría', 
        'Términos Pago', 'Moneda', 'Estado'
    ])
    
    # Datos
    clientes = Customer.objects.filter(status=True)
    for c in clientes:
        writer.writerow([
            c.id_customer,
            c.legal_name,
            c.name,
            c.tax_id,
            c.country,
            c.state_province,
            c.city,
            c.email,
            c.phone,
            c.category,
            c.payment_terms,
            c.currency,
            'Activo' if c.status else 'Inactivo'
        ])
    
    return response
```

---

### Consultas Avanzadas:
```python
from django.db.models import Count, Q
from customers.models import Customer

# Clientes por país (con conteo)
por_pais = Customer.objects.values('country').annotate(
    total=Count('id')
).order_by('-total')

for item in por_pais:
    print(f"{item['country']}: {item['total']}")

# Clientes por categoría
por_categoria = Customer.objects.values('category').annotate(
    total=Count('id')
).order_by('-total')

# Clientes por método de pago
por_metodo = Customer.objects.values(
    'payment_method__name'
).annotate(
    total=Count('id')
).order_by('-total')

# Clientes con órdenes de venta
from sales.models import SalesOrder

con_ordenes = Customer.objects.annotate(
    num_ordenes=Count('sales_orders')
).filter(num_ordenes__gt=0)

# Clientes sin órdenes
sin_ordenes = Customer.objects.annotate(
    num_ordenes=Count('sales_orders')
).filter(num_ordenes=0)

# Top 10 clientes con más órdenes
top_clientes = Customer.objects.annotate(
    num_ordenes=Count('sales_orders')
).order_by('-num_ordenes')[:10]

for c in top_clientes:
    print(f"{c.name}: {c.num_ordenes} órdenes")
```

---

## Notas Importantes

### ⚠️ **Advertencias:**

1. **No Eliminar Clientes con Órdenes:**
   - Genera error PROTECT
   - Pérdida de historial de ventas
   - Usar `status=False` en su lugar

2. **Validar IDs Únicos en CSV:**
   - Sistema rechaza duplicados
   - Revisar IDs antes de subir
   - Usar formato consistente (CUST-XXX)

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
   - CUST-001, CUST-002, etc.
   - Facilita búsqueda y orden
   - Evita conflictos

2. **Completar Todos los Datos:**
   - Más información = mejor gestión
   - Facilita reportes y análisis
   - Evita problemas en ventas

3. **Categorizar Clientes:**
   - Tecnología
   - Retail
   - Manufactura
   - Servicios
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
   customer.status = False
   customer.save()
   
   # ❌ Evitar
   customer.delete()
   ```

2. **Validar Antes de Guardar:**
   ```python
   from customers.forms import CustomerForm
   
   form = CustomerForm(data)
   if form.is_valid():
       form.save()
   else:
       print(form.errors)
   ```

3. **Usar Transacciones en Bulk:**
   ```python
   from django.db import transaction
   
   with transaction.atomic():
       Customer.objects.bulk_create(customers)
   ```

4. **Filtrar Activos por Defecto:**
   ```python
   # En vistas
   customers = Customer.objects.filter(status=True)
   ```

5. **Logging de Operaciones:**
   ```python
   import logging
   
   logger = logging.getLogger(__name__)
   logger.info(f"Cliente {customer.id_customer} creado por {user}")
   ```

---

### 🔧 **Mantenimiento:**

1. **Limpiar Clientes Duplicados:**
   ```python
   from django.db.models import Count
   
   duplicados = Customer.objects.values('tax_id').annotate(
       count=Count('id')
   ).filter(count__gt=1)
   
   for dup in duplicados:
       print(f"Tax ID duplicado: {dup['tax_id']}")
   ```

2. **Actualizar Información Masiva:**
   ```python
   # Cambiar moneda de todos los clientes de Ecuador
   Customer.objects.filter(country='Ecuador').update(
       currency='USD'
   )
   ```

3. **Auditoría de Datos:**
   ```python
   # Clientes sin email
   sin_email = Customer.objects.filter(
       Q(email__isnull=True) | Q(email='')
   )
   
   # Clientes sin categoría
   sin_categoria = Customer.objects.filter(
       Q(category__isnull=True) | Q(category='')
   )
   ```

4. **Verificar Integridad:**
   ```python
   # Clientes con método de pago inválido
   from suppliers.models import PaymentMethod
   
   invalidos = Customer.objects.exclude(
       payment_method__in=PaymentMethod.objects.all()
   )
   ```

---

## Resumen Técnico

**Modelos:** 1 (Customer) + PaymentMethod compartido  
**Vistas:** 6 (list, create, edit, delete, bulk_upload, download_template)  
**URLs:** 6  
**Formularios:** 2 (CustomerForm, CSVUploadForm)  
**Paginación:** 10 registros por página  
**Filtros:** 22 campos filtrables  
**Exportación:** CSV con todos los filtros  
**Carga Masiva:** CSV con delimitador `;`  
**Control de Permisos:** Superuser o role.customers ≥ 2  

**Campos del Modelo:** 21 campos totales
- Identificación: 4
- Ubicación: 5
- Contacto: 4
- Comercial: 6
- Control: 2

**Integraciones:**
- sales.SalesOrder (FK customer)
- suppliers.PaymentMethod (FK payment_method)
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

**Similitudes con Suppliers:**
- Estructura idéntica
- Mismo PaymentMethod
- Mismos formularios y validaciones
- Diferencia: Entidad comercial (cliente vs proveedor)
