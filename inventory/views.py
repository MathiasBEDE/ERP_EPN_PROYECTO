import csv
import random
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, F, Case, When, DecimalField, Count
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import InventoryMovement, InventoryLocation, MovementType
from .forms import InventoryAdjustmentForm


@login_required
def inventory_dashboard(request):
    """
    Vista principal del dashboard de inventario.
    Muestra estadísticas generales y accesos rápidos.
    """
    # Calcular estadísticas del módulo
    total_movements = InventoryMovement.objects.count()
    total_locations = InventoryLocation.objects.filter(status=True).count()
    
    # Obtener movimientos recientes
    recent_movements = InventoryMovement.objects.select_related(
        'material', 'location', 'movement_type'
    ).order_by('-movement_date')[:5]
    
    # Calcular stock total por ubicación
    movements_by_location = InventoryMovement.objects.values(
        'location__name'
    ).annotate(
        total_movements=Count('id')
    ).order_by('-total_movements')[:5]
    
    context = {
        'total_movements': total_movements,
        'total_locations': total_locations,
        'recent_movements': recent_movements,
        'movements_by_location': movements_by_location,
    }
    
    return render(request, 'inventory/dashboard.html', context)



def inventory_movement_list_view(request):
    """
    Vista para listar movimientos de inventario con filtros avanzados.
    Incluye búsqueda, filtros por material, ubicación, tipo y fechas.
    Soporta paginación y exportación a CSV.
    """
    # Obtener todos los movimientos con relaciones precargadas
    movements = InventoryMovement.objects.select_related(
        'material',
        'location',
        'unit_type',
        'movement_type',
        'created_by'
    )
    
    # Obtener parámetros de filtro
    q = request.GET.get('q', '').strip()
    material = request.GET.get('material', '').strip()
    location = request.GET.get('location', '').strip()
    type_filter = request.GET.get('type', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    # Aplicar filtro de búsqueda general (ID, material, referencia)
    if q:
        movements = movements.filter(
            Q(id_inventory_movement__icontains=q) |
            Q(material__id_material__icontains=q) |
            Q(material__name__icontains=q) |
            Q(reference__icontains=q)
        )
    
    # Filtrar por material
    if material:
        movements = movements.filter(
            Q(material__id_material__icontains=material) |
            Q(material__name__icontains=material)
        )
    
    # Filtrar por ubicación
    if location:
        try:
            location_id = int(location)
            movements = movements.filter(location_id=location_id)
        except ValueError:
            pass
    
    # Filtrar por tipo de movimiento
    if type_filter:
        movements = movements.filter(movement_type__symbol=type_filter)
    
    # Filtrar por fecha desde
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            movements = movements.filter(movement_date__gte=date_from_obj)
        except ValueError:
            messages.warning(request, 'Formato de fecha "Desde" inválido. Use AAAA-MM-DD.')
    
    # Filtrar por fecha hasta
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            movements = movements.filter(movement_date__lte=date_to_obj)
        except ValueError:
            messages.warning(request, 'Formato de fecha "Hasta" inválido. Use AAAA-MM-DD.')
    
    # Ordenar por fecha descendente (más recientes primero)
    movements = movements.order_by('-movement_date', '-id')
    
    # Manejar exportación a CSV
    export_format = request.GET.get('export', '').strip()
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="movimientos_inventario.csv"'
        
        # Escribir BOM para Excel
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'ID Movimiento',
            'Material ID',
            'Material Nombre',
            'Ubicación Código',
            'Ubicación Nombre',
            'Cantidad',
            'Unidad',
            'Tipo',
            'Fecha',
            'Referencia',
            'Creado Por'
        ])
        
        for movement in movements:
            # Determinar el signo según el tipo de movimiento
            quantity_str = str(movement.quantity)
            if movement.movement_type.symbol.endswith('_OUT'):
                quantity_str = f'-{quantity_str}'
            
            writer.writerow([
                movement.id_inventory_movement,
                movement.material.id_material,
                movement.material.name,
                movement.location.code,
                movement.location.name,
                quantity_str,
                movement.unit_type.symbol,
                movement.movement_type.name,
                movement.movement_date.strftime('%Y-%m-%d %H:%M:%S'),
                movement.reference or '',
                movement.created_by.username if movement.created_by else ''
            ])
        
        return response
    
    # Paginación
    paginator = Paginator(movements, 10)  # 10 movimientos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener datos para los filtros
    locations = InventoryLocation.objects.filter(status=True).order_by('name')
    movement_types = MovementType.objects.all().order_by('name')
    
    # Contexto para el template
    context = {
        'page_obj': page_obj,
        'movements': page_obj.object_list,
        'locations': locations,
        'movement_types': movement_types,
        'filters': {
            'q': q,
            'material': material,
            'location': location,
            'type': type_filter,
            'date_from': date_from,
            'date_to': date_to,
        },
        'total_count': paginator.count,
    }
    
    return render(request, 'inventory/inventory_movement_list.html', context)


def inventory_stock_view(request):
    """
    Vista para consultar el stock actual por material y ubicación.
    El stock se calcula a partir de los movimientos de inventario.
    Incluye filtros por material y ubicación, y exportación a CSV.
    """
    # Obtener todos los movimientos con relaciones precargadas
    movements = InventoryMovement.objects.select_related(
        'material',
        'location',
        'movement_type',
        'unit_type'
    )
    
    # Obtener parámetros de filtro
    q = request.GET.get('q', '').strip()
    location_filter = request.GET.get('location', '').strip()
    
    # Aplicar filtro de búsqueda por material
    if q:
        movements = movements.filter(
            Q(material__id_material__icontains=q) |
            Q(material__name__icontains=q)
        )
    
    # Filtrar por ubicación
    if location_filter:
        try:
            location_id = int(location_filter)
            movements = movements.filter(location_id=location_id)
        except ValueError:
            pass
    
    # Calcular el stock acumulado por (material, ubicación, unidad)
    stock_data = {}
    for m in movements:
        # Determinar el signo según el tipo de movimiento
        sign = -1 if m.movement_type.symbol.endswith('_OUT') else 1
        
        # Usar tupla (material, location, unit) como clave
        key = (m.material, m.location, m.unit_type)
        
        # Acumular la cantidad con el signo correspondiente
        stock_data[key] = stock_data.get(key, 0) + sign * m.quantity
    
    # Convertir a lista de diccionarios, excluyendo cantidades en 0
    stock_entries = []
    for (mat, loc, unit), qty in stock_data.items():
        if qty != 0:  # Solo mostrar existencias actuales (ignorar cantidades en 0)
            stock_entries.append({
                'material': mat,
                'location': loc,
                'unit': unit,
                'quantity': qty
            })
    
    # Ordenar por nombre de material y luego por ubicación
    stock_entries.sort(key=lambda entry: (entry['material'].name, entry['location'].name))
    
    # Manejar exportación a CSV
    export_format = request.GET.get('export', '').strip()
    if export_format == 'csv':
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="stock_inventario.csv"'
        
        # Escribir BOM para Excel
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'ID Material',
            'Material',
            'Código Ubicación',
            'Ubicación',
            'Cantidad',
            'Unidad'
        ])
        
        for entry in stock_entries:
            writer.writerow([
                entry['material'].id_material,
                entry['material'].name,
                entry['location'].code,
                entry['location'].name,
                entry['quantity'],
                entry['unit'].symbol
            ])
        
        return response
    
    # Paginación
    paginator = Paginator(stock_entries, 10)  # 10 entradas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener datos para los filtros
    locations = InventoryLocation.objects.filter(status=True).order_by('name')
    
    # Contexto para el template
    context = {
        'page_obj': page_obj,
        'stocks': page_obj.object_list,
        'locations': locations,
        'filters': {
            'q': q,
            'location': location_filter,
        },
        'total_count': paginator.count,
    }
    
    return render(request, 'inventory/inventory_stock.html', context)


def inventory_adjustment_view(request):
    """
    Vista para registrar ajustes manuales de inventario.
    Permite crear movimientos de tipo Ajuste (entrada o salida).
    """
    if request.method == 'POST':
        form = InventoryAdjustmentForm(request.POST)
        
        # Asignar unit_type antes de validar
        if form.is_bound and 'material' in form.data:
            try:
                material_id = form.data.get('material')
                if material_id:
                    from materials.models import Material
                    material = Material.objects.get(pk=material_id)
                    form.instance.unit_type = material.unit
            except (Material.DoesNotExist, ValueError):
                pass
        
        if form.is_valid():
            # Usar transacción atómica para garantizar consistencia
            try:
                with transaction.atomic():
                    # Crear el movimiento pero no guardar aún
                    movement = form.save(commit=False)
                    
                    # Generar ID único para el movimiento
                    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
                    unique_id = f"INV-{timestamp}-{random.randint(1000, 9999)}"
                    movement.id_inventory_movement = unique_id
                    
                    # La unidad ya fue asignada antes de la validación
                    # pero la reasignamos por seguridad
                    movement.unit_type = movement.material.unit
                    
                    # Asignar el usuario creador si está autenticado
                    if request.user.is_authenticated:
                        movement.created_by = request.user
                    
                    # Validar integridad antes de guardar
                    movement.full_clean()
                    
                    # Guardar el movimiento
                    movement.save()
                    
                    # Mensaje de éxito con detalles del ajuste
                    movement_type_display = "entrada" if movement.movement_type.symbol == "ADJUSTMENT_IN" else "salida"
                    messages.success(
                        request,
                        f'Ajuste de inventario registrado exitosamente: {movement.id_inventory_movement} - '
                        f'{movement.material.name} ({movement_type_display} de {movement.quantity} {movement.unit_type.symbol})'
                    )
                    
                    # Redirigir a la lista de movimientos
                    return redirect('inventory:inventory_movement_list')
                    
            except ValidationError as e:
                # Capturar errores de validación y agregarlos al formulario
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            form.add_error(field, error)
                else:
                    # Si es un error general (no asociado a un campo específico)
                    form.add_error(None, str(e))
                
                messages.error(request, 'No se pudo registrar el ajuste. Por favor verifique los datos.')
        else:
            # Si hay errores, se re-renderiza el formulario con los errores
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        # GET: Mostrar formulario vacío
        form = InventoryAdjustmentForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'inventory/inventory_adjustment_form.html', context)



