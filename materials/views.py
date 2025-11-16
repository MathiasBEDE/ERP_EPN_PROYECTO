from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse
from django.contrib import messages
import csv
import io
from .models import Material, Unit, MaterialType
from core.models import Status
from .forms import MaterialForm, CSVUploadForm

@login_required
def materials_list(request):
    materials = Material.objects.all()
    
    # Obtener filtros
    id_material = request.GET.get('id_material', '')
    name = request.GET.get('name', '')
    description = request.GET.get('description', '')
    unit_filter = request.GET.get('unit', '')
    type_filter = request.GET.get('type', '')
    status_filter = request.GET.get('status', '')
    created_at = request.GET.get('created_at', '')
    updated_at = request.GET.get('updated_at', '')
    created_by = request.GET.get('created_by', '')
    
    # Aplicar filtros
    if id_material:
        materials = materials.filter(id_material__icontains=id_material)
    if name:
        materials = materials.filter(name__icontains=name)
    if description:
        materials = materials.filter(description__icontains=description)
    if unit_filter:
        materials = materials.filter(Q(unit__name__icontains=unit_filter) | Q(unit__symbol__icontains=unit_filter))
    if type_filter:
        materials = materials.filter(Q(material_type__name__icontains=type_filter) | Q(material_type__symbol__icontains=type_filter))
    if status_filter:
        materials = materials.filter(status__id=status_filter)
    if created_at:
        materials = materials.filter(created_at__date=created_at)
    if updated_at:
        materials = materials.filter(updated_at__date=updated_at)
    if created_by:
        materials = materials.filter(created_by__username__icontains=created_by)
    
    # Exportar a CSV si se solicita
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="materials.csv"'
        
        writer = csv.writer(response, delimiter=';')
        writer.writerow(['ID Material', 'Nombre', 'Descripción', 'Unidad', 'Tipo', 'Estado', 'Fecha Creación', 'Fecha Actualización', 'Creado Por'])
        
        for material in materials:
            writer.writerow([
                material.id_material,
                material.name,
                material.description,
                material.unit.symbol if material.unit else 'N/A',
                material.material_type.name if material.material_type else 'N/A',
                material.status.name if material.status else 'N/A',
                material.created_at.strftime('%d/%m/%Y %H:%M'),
                material.updated_at.strftime('%d/%m/%Y %H:%M'),
                material.created_by.username if material.created_by else 'N/A'
            ])
        
        return response
    
    # Paginación
    paginator = Paginator(materials, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Construir querystring sin page
    querystring = request.GET.copy()
    if 'page' in querystring:
        querystring.pop('page')
    
    # Cargar opciones para los filtros
    units = Unit.objects.all()
    material_types = MaterialType.objects.all()
    statuses = Status.objects.all()
    
    filters = {
        'id_material': id_material,
        'name': name,
        'description': description,
        'unit': unit_filter,
        'type': type_filter,
        'status': status_filter,
        'created_at': created_at,
        'updated_at': updated_at,
        'created_by': created_by,
    }
    
    context = {
        'page_obj': page_obj,
        'filters': filters,
        'querystring': querystring.urlencode(),
        'units': units,
        'material_types': material_types,
        'statuses': statuses,
    }
    
    return render(request, 'materials/material_list.html', context)

@login_required
def material_create(request):
    if request.method == 'POST':
        form = MaterialForm(request.POST)
        if form.is_valid():
            material = form.save(commit=False)
            material.created_by = request.user
            material.save()
            return redirect('materials:material_create')
    else:
        form = MaterialForm()
    
    return render(request, 'materials/material_form.html', {'form': form})

@login_required
def material_edit(request, id):
    material = get_object_or_404(Material, id=id)
    
    if request.method == 'POST':
        form = MaterialForm(request.POST, instance=material)
        if form.is_valid():
            form.save()
            return redirect('materials:materials_list')
    else:
        form = MaterialForm(instance=material)
    
    context = {
        'form': form,
        'material': material,
        'edit_mode': True
    }
    return render(request, 'materials/material_form.html', context)

@login_required
def material_delete(request, id):
    material = get_object_or_404(Material, id=id)
    material.delete()
    return redirect('materials:materials_list')

@login_required
def material_bulk_upload(request):
    # Verificar permisos (permitir superusuarios)
    if not request.user.is_superuser:
        try:
            user_role = request.user.userrole_set.first()
            if not user_role or user_role.role.materials < 2:
                messages.error(request, 'You do not have permission to perform bulk uploads.')
                return redirect('materials:materials_list')
        except AttributeError:
            messages.error(request, 'You do not have permission to perform bulk uploads.')
            return redirect('materials:materials_list')
    
    if request.method == 'POST':
        form = CSVUploadForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            
            # Intentar decodificar el archivo
            try:
                decoded_file = csv_file.read().decode('utf-8')
            except UnicodeDecodeError:
                try:
                    csv_file.seek(0)
                    decoded_file = csv_file.read().decode('iso-8859-1')
                except Exception as e:
                    messages.error(request, f'Error decoding file: {str(e)}')
                    return render(request, 'materials/material_bulk_upload.html', {'form': form})
            
            # Construir diccionarios de mapeo
            status_map = {status.name.lower(): status.id for status in Status.objects.all()}
            unit_map = {}
            for unit in Unit.objects.all():
                unit_map[unit.symbol.lower()] = unit.id
                unit_map[unit.name.lower()] = unit.id
            type_map = {}
            for mt in MaterialType.objects.all():
                type_map[mt.symbol.lower()] = mt.id
                type_map[mt.name.lower()] = mt.id
            
            # Procesar CSV
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string, delimiter=';')
            
            # Limpiar BOM y espacios en cabeceras
            reader.fieldnames = [field.strip().replace('\ufeff', '') for field in reader.fieldnames]
            
            valid_materials = []
            error_rows = []
            row_number = 1
            
            for row in reader:
                row_number += 1
                # Limpiar espacios en valores
                cleaned_row = {k.strip(): v.strip() if isinstance(v, str) else v for k, v in row.items()}
                
                errors = []
                
                # Convertir unit de texto a ID
                if 'unit' in cleaned_row and cleaned_row['unit']:
                    unit_key = cleaned_row['unit'].lower()
                    if unit_key in unit_map:
                        cleaned_row['unit'] = unit_map[unit_key]
                    else:
                        errors.append(f"Unidad '{cleaned_row['unit']}' no encontrada")
                
                # Convertir type/material_type de texto a ID
                type_key_name = 'type' if 'type' in cleaned_row else 'material_type'
                if type_key_name in cleaned_row and cleaned_row[type_key_name]:
                    type_key = cleaned_row[type_key_name].lower()
                    if type_key in type_map:
                        cleaned_row['material_type'] = type_map[type_key]
                        if 'type' in cleaned_row:
                            del cleaned_row['type']
                    else:
                        errors.append(f"Tipo '{cleaned_row[type_key_name]}' no encontrado")
                
                # Convertir status de texto a ID
                if 'status' in cleaned_row and cleaned_row['status']:
                    status_key = cleaned_row['status'].lower()
                    if status_key in status_map:
                        cleaned_row['status'] = status_map[status_key]
                    else:
                        errors.append(f"Estado '{cleaned_row['status']}' no encontrado")
                
                # Si hay errores de conversión, agregar a error_rows
                if errors:
                    error_rows.append({
                        'row': row_number,
                        'data': cleaned_row,
                        'errors': {'conversion': errors}
                    })
                    continue
                
                # Crear formulario con los datos convertidos
                material_form = MaterialForm(cleaned_row)
                
                if material_form.is_valid():
                    material = material_form.save(commit=False)
                    material.created_by = request.user
                    valid_materials.append(material)
                else:
                    error_rows.append({
                        'row': row_number,
                        'data': cleaned_row,
                        'errors': material_form.errors
                    })
            
            # Guardar todos los registros válidos en una sola operación
            if valid_materials:
                Material.objects.bulk_create(valid_materials)
            
            # Preparar contexto con el informe
            context = {
                'form': form,
                'upload_complete': True,
                'total_rows': row_number - 1,
                'successful_rows': len(valid_materials),
                'error_count': len(error_rows),
                'error_rows': error_rows
            }
            
            if valid_materials:
                messages.success(request, f'Successfully uploaded {len(valid_materials)} materials.')
            if error_rows:
                messages.warning(request, f'{len(error_rows)} rows had errors and were not uploaded.')
            
            return render(request, 'materials/material_bulk_upload.html', context)
    else:
        form = CSVUploadForm()
    
    return render(request, 'materials/material_bulk_upload.html', {'form': form})

@login_required
def download_template_materials(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="materials_template.csv"'
    
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['id_material', 'name', 'description', 'unit', 'material_type', 'status'])
    writer.writerow(['MAT001', 'Material Ejemplo', 'Descripción del material', 'kg', 'Raw material', 'Active'])
    
    return response

