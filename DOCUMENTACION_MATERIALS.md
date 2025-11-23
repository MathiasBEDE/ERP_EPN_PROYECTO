# 📦 Módulo de Materiales (Materials)

## Descripción General
Módulo encargado de la gestión del catálogo de materiales del sistema ERP. Incluye funcionalidades de CRUD completo, filtros avanzados, exportación CSV y carga masiva de datos.

---

## Modelos Principales

### 1. **Unit** (Unidad de Medida)
Define las unidades de medida utilizadas en el sistema.

**Campos:**
- `name`: Nombre de la unidad (ej: Kilogramo, Metro) - CharField(100, unique=True)
- `symbol`: Símbolo de la unidad (ej: kg, m, L) - CharField(20)

**Métodos:**
- `__str__()`: Retorna formato "Name (Symbol)"
  ```python
  def __str__(self):
      return f"{self.name} ({self.symbol})"
  ```

**Tabla de Base de Datos:** `units`

**Ejemplos de Unidades:**
- Masa: Kilogramo (kg), Gramo (g), Libra (lb)
- Longitud: Metro (m), Centímetro (cm), Pulgada (in)
- Volumen: Litro (L), Mililitro (mL), Galón (gal)
- Cantidad: Unidad (unid), Pieza (pza), Caja (caja)

---

### 2. **MaterialType** (Tipo de Material)
Clasificación de materiales según su naturaleza.

**Campos:**
- `name`: Nombre del tipo (ej: Materia Prima, Producto Terminado) - CharField(100, unique=True)
- `symbol`: Símbolo identificador (ej: MP, PT) - CharField(20)

**Métodos:**
- `__str__()`: Retorna formato "Name (Symbol)"
  ```python
  def __str__(self):
      return f"{self.name} ({self.symbol})"
  ```

**Tabla de Base de Datos:** `material_types`

**Ejemplos de Tipos:**
- Raw material (MP) - Materia Prima
- Finished product (PT) - Producto Terminado
- Semi-finished (SF) - Semi-elaborado
- Consumable (CON) - Consumible
- Spare part (SP) - Repuesto

---

### 3. **Material** (Material/Producto)
Catálogo completo de materiales del sistema.

**Campos:**
- `id_material`: Código único identificador del material - CharField(50, unique=True)
- `name`: Nombre descriptivo del material - CharField(200)
- `description`: Descripción detallada - TextField
- `unit`: Unidad de medida - ForeignKey(Unit, on_delete=PROTECT, default=1)
- `material_type`: Tipo de material - ForeignKey(MaterialType, on_delete=PROTECT, default=1)
- `status`: Estado del material - ForeignKey(Status, on_delete=PROTECT, default=1)
- `created_at`: Fecha de creación - DateTimeField(auto_now_add=True)
- `updated_at`: Fecha de última actualización - DateTimeField(auto_now=True)
- `created_by`: Usuario creador - ForeignKey(User, on_delete=SET_NULL, null=True, blank=True)

**Métodos:**
- `__str__()`: Retorna formato "ID - Name"
  ```python
  def __str__(self):
      return f"{self.id_material} - {self.name}"
  ```

**Tabla de Base de Datos:** `materials`

**Validaciones:**
- `id_material` debe ser único
- `unit` debe existir (PROTECT: no se puede eliminar unidad en uso)
- `material_type` debe existir (PROTECT: no se puede eliminar tipo en uso)
- `status` debe existir (PROTECT: no se puede eliminar estado en uso)

---

## Formularios

### **MaterialForm**
Formulario para crear y editar materiales.

**Campos incluidos:**
- `id_material`: Campo de texto con placeholder
- `name`: Campo de texto con placeholder
- `description`: Textarea de 4 filas
- `unit`: Select de unidades
- `material_type`: Select de tipos de material
- `status`: Select de estados

**Widgets con Tailwind CSS:**
Todos los campos tienen clases CSS para diseño responsive:
```python
'class': 'w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500'
```

---

### **CSVUploadForm**
Formulario para carga masiva de materiales desde archivo CSV.

**Campos:**
- `csv_file`: FileField con accept='.csv'

**Configuración:**
- Help text: "Upload a CSV file with material data. Download the template to see the required format."
- Acepta solo archivos .csv
- Separador: punto y coma (;)

---

## URLs Disponibles

```python
/materials/                           # Lista de materiales
/materials/create/                    # Crear nuevo material
/materials/<id>/edit/                 # Editar material
/materials/<id>/delete/               # Eliminar material
/materials/bulk-upload/               # Carga masiva CSV
/materials/bulk-upload/template/      # Descargar plantilla CSV
```

---

## Vistas (Views)

### 1. **materials_list**
Lista paginada de materiales con filtros avanzados y exportación CSV.

**Funcionalidades:**
- ✅ Paginación (10 registros por página)
- ✅ Filtros por todos los campos
- ✅ Exportación a CSV
- ✅ Búsqueda por texto en múltiples campos

**Filtros Disponibles:**
- `id_material`: Búsqueda parcial (icontains)
- `name`: Búsqueda parcial (icontains)
- `description`: Búsqueda parcial (icontains)
- `unit`: Búsqueda en nombre o símbolo de unidad
- `type`: Búsqueda en nombre o símbolo de tipo
- `status`: Filtro exacto por ID de estado
- `created_at`: Filtro por fecha exacta
- `updated_at`: Filtro por fecha exacta
- `created_by`: Búsqueda parcial en username

**Exportación CSV:**
- Parámetro: `?export=csv`
- Separador: punto y coma (;)
- Columnas: ID Material, Nombre, Descripción, Unidad, Tipo, Estado, Fecha Creación, Fecha Actualización, Creado Por
- Formato de fechas: dd/mm/yyyy HH:MM

**Ejemplo de uso:**
```
/materials/?name=acero&type=mp&export=csv
```

---

### 2. **material_create**
Crea un nuevo material.

**Proceso:**
1. Muestra formulario vacío (GET)
2. Valida datos (POST)
3. Asigna `created_by = request.user` automáticamente
4. Guarda en base de datos
5. Redirige a formulario de creación (permite crear múltiples)

**Decorador:** `@login_required`

---

### 3. **material_edit**
Edita un material existente.

**Proceso:**
1. Obtiene material por ID o retorna 404
2. Muestra formulario pre-llenado (GET)
3. Valida cambios (POST)
4. Actualiza registro
5. Redirige a lista de materiales

**Decorador:** `@login_required`

**Context adicional:**
- `edit_mode = True`: Indica modo edición en template

---

### 4. **material_delete**
Elimina un material.

**Proceso:**
1. Obtiene material por ID o retorna 404
2. Elimina registro de base de datos
3. Redirige a lista de materiales

**Decorador:** `@login_required`

⚠️ **Advertencia:** Eliminación física, sin soft-delete.

---

### 5. **material_bulk_upload**
Carga masiva de materiales desde archivo CSV.

**Permisos requeridos:**
- Superusuario (`is_superuser=True`), o
- UserRole con `materials >= 2`

**Proceso:**
1. Valida permisos de usuario
2. Recibe archivo CSV (POST)
3. Decodifica archivo (UTF-8 o ISO-8859-1 como fallback)
4. Construye mapeos de Status, Unit, MaterialType
5. Procesa fila por fila:
   - Limpia espacios en valores
   - Convierte textos a IDs (unit, type, status)
   - Valida con MaterialForm
   - Acumula válidos y errores
6. Guarda registros válidos con `bulk_create()`
7. Muestra informe de resultados

**Mapeos automáticos:**
- **Status:** Por nombre (case-insensitive)
- **Unit:** Por símbolo o nombre (case-insensitive)
- **MaterialType:** Por símbolo o nombre (case-insensitive)

**Formato del CSV:**
```csv
id_material;name;description;unit;material_type;status
MAT001;Material Ejemplo;Descripción del material;kg;Raw material;Active
```

**Informe de resultados:**
- Total de filas procesadas
- Registros exitosos
- Registros con errores
- Detalle de errores por fila

**Mensajes:**
- ✅ Success: "Successfully uploaded X materials."
- ⚠️ Warning: "X rows had errors and were not uploaded."
- ❌ Error: "You do not have permission to perform bulk uploads."

---

### 6. **download_template_materials**
Descarga plantilla CSV para carga masiva.

**Contenido:**
- Cabecera con nombres de campos
- Fila de ejemplo con datos válidos
- Separador: punto y coma (;)

**Nombre del archivo:** `materials_template.csv`

**Decorador:** `@login_required`

---

## Flujo de Trabajo Típico

### 1. Creación Manual de Material

**Paso 1: Acceder al formulario**
```
/materials/create/
```

**Paso 2: Completar datos**
- ID Material: Código único (ej: MAT-001, ACERO-304)
- Nombre: Descripción corta
- Descripción: Detalles completos del material
- Unidad: Seleccionar de lista
- Tipo: Seleccionar de lista (MP, PT, etc.)
- Estado: Seleccionar de lista (Active, Inactive, etc.)

**Paso 3: Guardar**
- Sistema asigna usuario creador automáticamente
- Timestamps se generan automáticamente
- Redirige a formulario para crear otro material

---

### 2. Carga Masiva CSV

**Paso 1: Descargar plantilla**
```
/materials/bulk-upload/template/
```

**Paso 2: Completar Excel/CSV**
```csv
id_material;name;description;unit;material_type;status
ACERO-304;Acero Inoxidable 304;Lámina acero inoxidable calibre 20;kg;Raw material;Active
TORNILLO-M8;Tornillo M8x20;Tornillo hexagonal métrico 8x20mm;pza;Spare part;Active
PINTURA-AZ;Pintura Azul;Pintura esmalte sintético azul cielo;L;Consumable;Active
```

**Paso 3: Subir archivo**
```
/materials/bulk-upload/
```

**Paso 4: Revisar informe**
- ✅ Registros exitosos: Se crearon en BD
- ❌ Registros con error: Revisar detalle de error
- Corregir errores y volver a subir

---

### 3. Búsqueda y Filtrado

**Búsqueda simple por nombre:**
```
/materials/?name=acero
```

**Filtros combinados:**
```
/materials/?type=raw&status=1&name=acero
```

**Exportar resultados filtrados:**
```
/materials/?type=raw&export=csv
```

---

### 4. Edición de Material

**Paso 1: Acceder desde lista**
- Click en botón "Editar" del material deseado

**Paso 2: Modificar datos**
- Todos los campos son editables excepto timestamps
- `created_by` no se modifica

**Paso 3: Guardar cambios**
- `updated_at` se actualiza automáticamente

---

### 5. Eliminación de Material

**Paso 1: Acceder desde lista**
- Click en botón "Eliminar" del material deseado

**Paso 2: Confirmación**
- (Implementar modal de confirmación en frontend)

**Paso 3: Eliminación**
- Registro se elimina de BD permanentemente

⚠️ **Cuidado:** Si el material está referenciado en otras tablas (órdenes, inventario, BOM), puede fallar por restricción de integridad referencial.

---

## Reglas de Negocio

### 1. **Unicidad de ID Material**
- `id_material` debe ser único en todo el sistema
- Sistema previene duplicados a nivel de base de datos
- Recomendable usar nomenclatura estándar y consistente

### 2. **Protección de Referencias**
- `Unit`, `MaterialType`, y `Status` tienen `on_delete=PROTECT`
- No se pueden eliminar si hay materiales que los usan
- Garantiza integridad referencial

### 3. **Auditoría Automática**
- `created_at`: Se asigna automáticamente al crear
- `updated_at`: Se actualiza automáticamente al editar
- `created_by`: Se asigna automáticamente al crear

### 4. **Estados de Material**
- Depende de registros en tabla `status` (core)
- Ejemplo: Active, Inactive, Discontinued
- Permite filtrado y control de materiales obsoletos

### 5. **Clasificación por Tipo**
- Permite agrupar materiales por naturaleza
- Facilita reportes y búsquedas
- Útil para diferentes procesos: compras, ventas, producción

---

## Integraciones con Otros Módulos

### **Core**
- Usa modelo `Status` para estados de material
- Usa modelo `Currency` (indirectamente en precios futuros)
- Usa modelo `Country` (para origen/destino futuros)

### **Users**
- Campo `created_by` referencia usuario creador
- Control de permisos para carga masiva

### **Inventory**
- Materiales se usan en movimientos de inventario
- Unidades de medida compartidas

### **Purchases**
- Materiales comprables en órdenes de compra
- Precios y proveedores por material

### **Sales**
- Materiales vendibles en órdenes de venta
- Precios de venta por material

### **Manufacturing**
- Materiales en listas de materiales (BOM)
- Consumo y producción de materiales

---

## Permisos y Roles

### **Permisos de Django:**
- `materials.view_material` - Ver lista de materiales
- `materials.add_material` - Crear material
- `materials.change_material` - Editar material
- `materials.delete_material` - Eliminar material

### **Permisos Especiales:**
- **Carga Masiva CSV:** Requiere `is_superuser=True` o `UserRole.materials >= 2`

### **Decoradores:**
- Todas las vistas usan `@login_required`
- Usuario no autenticado es redirigido a login

---

## Ejemplos de Código

### Crear Material Programáticamente:
```python
from materials.models import Material, Unit, MaterialType
from core.models import Status
from users.models import User

# Obtener referencias
unidad_kg = Unit.objects.get(symbol='kg')
tipo_mp = MaterialType.objects.get(symbol='MP')
estado_activo = Status.objects.get(name='Active')
usuario = User.objects.get(username='admin')

# Crear material
material = Material.objects.create(
    id_material='ACERO-304',
    name='Acero Inoxidable 304',
    description='Lámina de acero inoxidable calibre 20',
    unit=unidad_kg,
    material_type=tipo_mp,
    status=estado_activo,
    created_by=usuario
)

print(f"Material creado: {material}")
# Output: Material creado: ACERO-304 - Acero Inoxidable 304
```

---

### Buscar Materiales:
```python
from materials.models import Material

# Todos los materiales activos
activos = Material.objects.filter(status__name='Active')

# Buscar por ID parcial
materiales_acero = Material.objects.filter(id_material__icontains='ACERO')

# Buscar por nombre
materiales = Material.objects.filter(name__icontains='tornillo')

# Filtrar por tipo
materias_primas = Material.objects.filter(material_type__symbol='MP')

# Filtrar por unidad
materiales_kg = Material.objects.filter(unit__symbol='kg')

# Ordenar por fecha de creación (más recientes primero)
recientes = Material.objects.all().order_by('-created_at')[:10]
```

---

### Actualizar Material:
```python
material = Material.objects.get(id_material='ACERO-304')

# Cambiar nombre
material.name = 'Acero Inoxidable AISI 304'
material.save()
# updated_at se actualiza automáticamente

# Cambiar estado
estado_inactivo = Status.objects.get(name='Inactive')
material.status = estado_inactivo
material.save()
```

---

### Eliminar Material:
```python
material = Material.objects.get(id_material='ACERO-304')

# Verificar si está en uso (opcional, manual)
# Si tiene referencias, la BD generará error de integridad

material.delete()
```

---

### Obtener Estadísticas:
```python
from materials.models import Material
from django.db.models import Count

# Total de materiales
total = Material.objects.count()

# Materiales por tipo
por_tipo = Material.objects.values('material_type__name').annotate(
    total=Count('id')
).order_by('-total')

for item in por_tipo:
    print(f"{item['material_type__name']}: {item['total']}")

# Materiales por estado
por_estado = Material.objects.values('status__name').annotate(
    total=Count('id')
)

# Materiales por unidad
por_unidad = Material.objects.values('unit__symbol').annotate(
    total=Count('id')
).order_by('-total')
```

---

### Exportar Materiales Filtrados:
```python
import csv
from django.http import HttpResponse
from materials.models import Material

def export_filtered_materials(queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="materials_export.csv"'
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['ID Material', 'Nombre', 'Descripción', 'Unidad', 'Tipo', 'Estado'])
    
    for material in queryset:
        writer.writerow([
            material.id_material,
            material.name,
            material.description,
            material.unit.symbol,
            material.material_type.name,
            material.status.name
        ])
    
    return response

# Uso
materiales_activos = Material.objects.filter(status__name='Active')
response = export_filtered_materials(materiales_activos)
```

---

### Validar Datos Antes de Crear:
```python
from materials.forms import MaterialForm

# Simular datos POST
data = {
    'id_material': 'TEST-001',
    'name': 'Material de Prueba',
    'description': 'Descripción de prueba',
    'unit': 1,  # ID de unidad
    'material_type': 1,  # ID de tipo
    'status': 1  # ID de estado
}

form = MaterialForm(data)

if form.is_valid():
    material = form.save(commit=False)
    material.created_by = request.user
    material.save()
    print(f"✅ Material creado: {material}")
else:
    print(f"❌ Errores de validación:")
    for field, errors in form.errors.items():
        print(f"  - {field}: {', '.join(errors)}")
```

---

## Notas Importantes

### ⚠️ **Advertencias:**

1. **Eliminación Física:**
   - Los materiales se eliminan permanentemente de la BD
   - No hay soft-delete ni papelera de reciclaje
   - Verificar referencias antes de eliminar

2. **Integridad Referencial:**
   - Unit, MaterialType, Status con `PROTECT`
   - No se pueden eliminar si hay materiales usándolos
   - Planificar bien la estructura inicial

3. **Permisos de Carga Masiva:**
   - Solo superusuarios o roles con `materials >= 2`
   - Validar permisos antes de dar acceso

4. **Duplicados en CSV:**
   - Si un `id_material` existe, la carga falla para esa fila
   - Revisar BD antes de carga masiva
   - Usar modo "update" si se necesita actualizar

5. **Formato de CSV:**
   - Separador: punto y coma (;)
   - Codificación: UTF-8 (fallback a ISO-8859-1)
   - Nombres de campos exactos

---

### 💡 **Tips:**

1. **Nomenclatura de IDs:**
   - Usar prefijos por tipo: `MP-`, `PT-`, `SF-`
   - Incluir código descriptivo: `ACERO-304`, `TORNILLO-M8`
   - Evitar espacios, usar guiones

2. **Descripciones Completas:**
   - Incluir especificaciones técnicas
   - Normas aplicables (ISO, ASTM, etc.)
   - Dimensiones, grado, acabado

3. **Unidades Estándar:**
   - Definir unidades comunes al inicio
   - Usar símbolos reconocidos internacionalmente
   - Evitar ambigüedades (L vs l, m vs M)

4. **Tipos Lógicos:**
   - Crear tipos según procesos del negocio
   - No crear demasiados tipos (mantener simple)
   - Usar símbolos cortos y claros

5. **Estados Útiles:**
   - Active: Material en uso normal
   - Inactive: Temporalmente no disponible
   - Discontinued: Ya no se usa, mantener por historial
   - Obsolete: Obsoleto, reemplazado por otro

6. **Carga Masiva Eficiente:**
   - Preparar datos en Excel antes de CSV
   - Validar datos antes de subir
   - Corregir errores y volver a intentar
   - Usar plantilla como referencia

---

### 📊 **Mejores Prácticas:**

1. **Catálogo Limpio:**
   - Revisar periódicamente materiales obsoletos
   - Cambiar estado en lugar de eliminar
   - Mantener descripciones actualizadas

2. **Búsquedas Eficientes:**
   - Usar filtros combinados
   - Exportar resultados filtrados
   - Guardar criterios de búsqueda frecuentes

3. **Auditoría:**
   - Revisar quién creó cada material
   - Analizar fechas de creación/actualización
   - Detectar duplicados por nombre similar

4. **Capacitación:**
   - Entrenar usuarios en nomenclatura estándar
   - Documentar convenciones de nombres
   - Validar datos antes de cargas masivas

5. **Respaldos:**
   - Exportar catálogo completo regularmente
   - Mantener versiones históricas
   - Documentar cambios importantes

---

### 🔧 **Mantenimiento:**

1. **Limpieza de Datos:**
   ```python
   # Materiales duplicados por nombre
   from django.db.models import Count
   duplicados = Material.objects.values('name').annotate(
       count=Count('id')
   ).filter(count__gt=1)
   ```

2. **Materiales Sin Uso:**
   ```python
   # Identificar materiales creados hace más de 1 año sin uso
   from django.utils import timezone
   from datetime import timedelta
   
   un_ano_atras = timezone.now() - timedelta(days=365)
   viejos = Material.objects.filter(
       created_at__lt=un_ano_atras,
       # Agregar condiciones de uso de otros módulos
   )
   ```

3. **Actualización Masiva:**
   ```python
   # Cambiar estado de múltiples materiales
   estado_inactivo = Status.objects.get(name='Inactive')
   Material.objects.filter(
       id_material__startswith='OLD-'
   ).update(status=estado_inactivo)
   ```

4. **Migración de Datos:**
   - Planificar cambios de estructura
   - Crear scripts de migración
   - Probar en entorno de desarrollo
   - Respaldar antes de ejecutar en producción

---

## Campos Futuros (Extensión Recomendada)

Para un sistema ERP completo, considerar agregar:

```python
class Material(models.Model):
    # ... campos actuales ...
    
    # Precios
    standard_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Control de stock
    min_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_stock = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Clasificación
    is_purchasable = models.BooleanField(default=True)
    is_saleable = models.BooleanField(default=True)
    is_manufacturable = models.BooleanField(default=False)
    
    # Adicionales
    barcode = models.CharField(max_length=50, blank=True, null=True)
    internal_reference = models.CharField(max_length=100, blank=True, null=True)
    supplier_reference = models.CharField(max_length=100, blank=True, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    volume = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    
    # Imágenes
    image = models.ImageField(upload_to='materials/', blank=True, null=True)
```

---

## Resumen Técnico

**Modelos:** 3 (Unit, MaterialType, Material)  
**Vistas:** 6 (list, create, edit, delete, bulk_upload, template)  
**Formularios:** 2 (MaterialForm, CSVUploadForm)  
**URLs:** 6  
**Templates requeridos:** 3 (list, form, bulk_upload)  
**Permisos:** 4 + 1 especial (bulk upload)  
**Exportación:** CSV con separador ;  
**Importación:** CSV masiva con validación  
**Paginación:** 10 registros por página  
**Filtros:** 9 campos diferentes  

**Dependencias:**
- core.Status
- users.User
- Django auth decorators
