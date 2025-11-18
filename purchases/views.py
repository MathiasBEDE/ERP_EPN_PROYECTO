from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator
from suppliers.models import Supplier
from materials.models import Material
from materials.models import Unit
from core.models import Currency
from .models import PurchaseOrder, PurchaseOrderLine, OrderStatus
from inventory.utils import create_inventory_movements_for_purchase_order
from inventory.models import InventoryLocation, MovementType
from datetime import date
import json
import logging
import csv

# Configure logger
logger = logging.getLogger(__name__)

# Vista de detalle de orden de compra
def purchase_order_detail_view(request, order_id):
    """
    Vista que muestra el detalle completo de una orden de compra.
    También maneja las acciones de cambio de estado (Recibir, Cancelar, Cerrar).
    
    URL: /purchases/purchase-order/<order_id>/
    Método: GET, POST
    Parámetro: order_id es el identificador único de la orden (ej: PO-0001)
    
    Acciones POST:
        - receive: Marca la orden como recibida y actualiza cantidades
        - cancel: Cancela la orden
        - close: Cierra la orden administrativamente
    
    Retorna:
        - HTML con el detalle de la orden de compra
        - 404 si la orden no existe
    """
    
    # Mapeo de acciones a símbolos de estado (usar símbolos reales de la BD)
    ACTION_STATUS_MAP = {
        "receive": "RECEIVED",    # Fully Received
        "cancel": "CANCELLED",    # Cancelled
        "close": "CLOSED"         # Closed
    }
    
    try:
        # Obtener la orden con todas sus relaciones optimizadas
        order = PurchaseOrder.objects.select_related(
            'supplier', 
            'status', 
            'created_by'
        ).prefetch_related(
            'lines__material',
            'lines__unit_material',
            'lines__currency_supplier'
        ).get(id_purchase_order=order_id)
        
        # Manejar acciones POST
        if request.method == 'POST':
            action = request.POST.get('action')
            
            # Validar que la acción sea válida
            status_symbol = ACTION_STATUS_MAP.get(action)
            if not status_symbol:
                messages.error(request, 'Acción no válida.')
                return redirect('purchases:purchase_order_detail', order_id=order.id_purchase_order)
            
            # Obtener el estado destino
            try:
                new_status = OrderStatus.objects.get(symbol=status_symbol)
            except OrderStatus.DoesNotExist:
                messages.error(
                    request,
                    f'Estado "{status_symbol}" no encontrado en el sistema. '
                    f'Por favor, verifique que el estado existe en la configuración.'
                )
                return redirect('purchases:purchase_order_detail', order_id=order.id_purchase_order)
            
            # Aplicar lógica específica por acción
            if action == 'receive':
                # Solo permitir recibir si está en DRAFT o CONFIRMED
                if order.status.symbol not in ['DRAFT', 'CONFIRMED']:
                    messages.error(
                        request, 
                        f'No se puede recibir una orden en estado "{order.status.name}". '
                        f'Debe estar en estado Draft o Confirmed.'
                    )
                    return redirect('purchases:purchase_order_detail', order_id=order.id_purchase_order)
                
                # Marcar todas las líneas como totalmente recibidas y crear movimientos de inventario
                try:
                    with transaction.atomic():
                        # Actualizar cantidades recibidas en todas las líneas
                        for line in order.lines.all():
                            line.received_quantity = line.quantity
                            line.save()
                        
                        # Cambiar estado a RECEIVED
                        order.status = new_status
                        order.save()
                        
                        # Crear movimientos de inventario
                        created_movements = create_inventory_movements_for_purchase_order(
                            order, 
                            user=request.user if request.user.is_authenticated else None
                        )
                        
                        num_movements = len(created_movements)
                        messages.success(
                            request, 
                            f'Orden {order.id_purchase_order} marcada como recibida. '
                            f'Se crearon {num_movements} movimiento(s) de inventario.'
                        )
                
                except InventoryLocation.DoesNotExist:
                    messages.error(
                        request,
                        'No se pudo actualizar el inventario: No hay ubicaciones de inventario configuradas. '
                        'Contacte al administrador del sistema.'
                    )
                    logger.error(f'No inventory locations found when receiving order {order.id_purchase_order}')
                    
                except MovementType.DoesNotExist:
                    messages.error(
                        request,
                        'No se pudo actualizar el inventario: Tipo de movimiento PURCHASE_IN no encontrado. '
                        'Ejecute el comando init_movement_types.'
                    )
                    logger.error(f'MovementType PURCHASE_IN not found when receiving order {order.id_purchase_order}')
                    
                except Exception as e:
                    messages.error(
                        request,
                        f'Error al actualizar inventario: {str(e)}. Contacte al administrador.'
                    )
                    logger.exception(f'Error creating inventory movements for order {order.id_purchase_order}')
                
                return redirect('purchases:purchase_order_detail', order_id=order.id_purchase_order)
            
            elif action == 'cancel':
                # Solo permitir cancelar si está en DRAFT o CONFIRMED
                if order.status.symbol not in ['DRAFT', 'CONFIRMED']:
                    messages.error(
                        request, 
                        f'No se puede cancelar una orden en estado "{order.status.name}". '
                        f'Solo se pueden cancelar órdenes en Draft o Confirmed.'
                    )
                    return redirect('purchases:purchase_order_detail', order_id=order.id_purchase_order)
                
                with transaction.atomic():
                    order.status = new_status
                    order.save()
                
                messages.success(
                    request, 
                    f'Orden {order.id_purchase_order} cancelada exitosamente.'
                )
                return redirect('purchases:purchase_order_detail', order_id=order.id_purchase_order)
            
            elif action == 'close':
                # Solo permitir cerrar si está RECEIVED
                if order.status.symbol != 'RECEIVED':
                    messages.error(
                        request, 
                        f'Solo se puede cerrar una orden en estado "Fully Received". '
                        f'Estado actual: {order.status.name}.'
                    )
                    return redirect('purchases:purchase_order_detail', order_id=order.id_purchase_order)
                
                with transaction.atomic():
                    order.status = new_status
                    order.save()
                
                messages.success(
                    request, 
                    f'Orden {order.id_purchase_order} cerrada exitosamente.'
                )
                return redirect('purchases:purchase_order_detail', order_id=order.id_purchase_order)
        
        # Determinar qué acciones están disponibles según el estado actual
        available_actions = {
            'can_receive': order.status.symbol in ['DRAFT', 'CONFIRMED'],
            'can_cancel': order.status.symbol in ['DRAFT', 'CONFIRMED'],
            'can_close': order.status.symbol == 'RECEIVED',
        }
        
        context = {
            'order': order,
            'available_actions': available_actions,
        }
        
        return render(request, 'purchases/purchase_order_detail.html', context)
        
    except PurchaseOrder.DoesNotExist:
        raise Http404(f"Orden de compra '{order_id}' no encontrada")

# Vista de lista de órdenes de compra
def purchase_order_list_view(request):
    """
    Vista que muestra la lista de todas las órdenes de compra con filtros y paginación.
    También permite exportar los resultados a CSV.
    
    URL: /purchases/purchase-order/
    Método: GET
    
    Filtros opcionales (GET):
        - q: Buscar por ID de orden (PO-0001)
        - supplier: Filtrar por ID de proveedor
        - status: Filtrar por símbolo de estado
        - date_from: Fecha de emisión desde (YYYY-MM-DD)
        - date_to: Fecha de emisión hasta (YYYY-MM-DD)
        - page: Número de página para paginación
        - export: Si es "csv", exporta los resultados filtrados a CSV
    
    Retorna:
        - HTML con la lista paginada de órdenes de compra
        - CSV descargable si export=csv
    """
    # Obtener todas las órdenes con sus relaciones optimizadas
    orders = PurchaseOrder.objects.select_related('supplier', 'status', 'created_by').all()
    
    # Leer parámetros de filtro
    q = request.GET.get('q', '').strip()
    supplier_id = request.GET.get('supplier', '').strip()
    status_symbol = request.GET.get('status', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    export_format = request.GET.get('export', '').strip()
    
    # Aplicar filtros condicionalmente
    if q:
        # Buscar por ID de orden o nombre de proveedor
        orders = orders.filter(
            Q(id_purchase_order__icontains=q) |
            Q(supplier__name__icontains=q)
        )
    
    if supplier_id:
        # Filtrar por ID de proveedor (id_supplier field)
        orders = orders.filter(supplier__id_supplier__icontains=supplier_id)
    
    if status_symbol:
        # Filtrar por símbolo de estado
        orders = orders.filter(status__symbol=status_symbol)
    
    if date_from:
        # Filtrar desde fecha de emisión
        try:
            orders = orders.filter(issue_date__gte=date_from)
        except ValueError:
            messages.warning(request, 'Formato de fecha "Desde" inválido.')
    
    if date_to:
        # Filtrar hasta fecha de emisión
        try:
            orders = orders.filter(issue_date__lte=date_to)
        except ValueError:
            messages.warning(request, 'Formato de fecha "Hasta" inválido.')
    
    # Ordenar por fecha de creación descendente (más recientes primero)
    orders = orders.order_by('-created_at')
    
    # Si se solicita exportación CSV, generar el archivo
    if export_format == 'csv':
        # Preparar respuesta CSV
        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="ordenes_compra.csv"'
        
        # Escribir BOM para UTF-8 (ayuda a Excel a detectar encoding)
        response.write('\ufeff')
        
        writer = csv.writer(response)
        
        # Escribir encabezados
        writer.writerow([
            'ID Orden',
            'Proveedor ID',
            'Proveedor Nombre',
            'Estado',
            'Fecha Emisión',
            'Fecha Estimada Entrega',
            'Total Orden (USD)',
            'Creado Por',
            'Fecha Creación'
        ])
        
        # Escribir filas de datos
        for order in orders:
            writer.writerow([
                order.id_purchase_order,
                order.supplier.id_supplier,
                order.supplier.name,
                order.status.name,
                order.issue_date.strftime('%Y-%m-%d') if order.issue_date else '',
                order.estimated_delivery_date.strftime('%Y-%m-%d') if order.estimated_delivery_date else '',
                f'{order.get_total_amount():.2f}',
                order.created_by.username if order.created_by else '',
                order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else ''
            ])
        
        return response
    
    # Aplicar paginación (10 órdenes por página)
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener listas para los selectores de filtro
    statuses = OrderStatus.objects.all().order_by('name')
    suppliers = Supplier.objects.all().order_by('name')
    
    # Preparar contexto
    context = {
        'page_obj': page_obj,
        'orders': page_obj.object_list,
        'statuses': statuses,
        'suppliers': suppliers,
        'filters': {
            'q': q,
            'supplier': supplier_id,
            'status': status_symbol,
            'date_from': date_from,
            'date_to': date_to,
        },
        'total_count': paginator.count,
    }
    
    return render(request, 'purchases/purchase_order_list.html', context)

# Vista del formulario de creación de pedido de compra
def purchase_order_form_view(request):
    """
    Vista que renderiza el formulario para crear una nueva orden de compra.
    
    URL: /purchases/create/
    Método: GET
    
    Retorna:
        - HTML con el formulario de creación de pedido
    """
    context = {
        'currencies': Currency.objects.all().order_by('code'),
        'today': date.today().strftime('%Y-%m-%d'),
    }
    
    return render(request, 'purchases/purchase_order_create.html', context)

# API para obtener detalles de proveedor
def supplier_detail_api(request, supplier_id):
    """
    API endpoint que devuelve los datos de un proveedor en formato JSON.
    
    URL: /purchases/api/supplier/<supplier_id>/
    Método: GET
    Parámetro: supplier_id puede ser el ID numérico o el id_supplier (ej: SUP-001)
    
    Retorna:
        - 200: JSON con los datos del proveedor
        - 404: Si el proveedor no existe
    """
    try:
        # Intentar buscar por id_supplier primero (string como SUP-001)
        try:
            supplier = Supplier.objects.get(id_supplier=supplier_id)
        except Supplier.DoesNotExist:
            # Si falla, intentar por ID numérico
            supplier = Supplier.objects.get(id=int(supplier_id))
        
        data = {
            'supplier_id': supplier.id,
            'id_supplier': supplier.id_supplier,
            'name': supplier.name,
            'address': supplier.address,
            'city': supplier.city,
            'state_province': supplier.state_province,
            'country': supplier.country,
            'postal_code': supplier.zip_code,
            'phone': supplier.phone,
            'email': supplier.email,
            'contact_person': supplier.contact_name,
            'tax_id': supplier.tax_id,
            'payment_method': supplier.payment_method.name if supplier.payment_method else None,
        }
        
        return JsonResponse(data)
    
    except (Supplier.DoesNotExist, ValueError):
        raise Http404("Proveedor no encontrado")

# API para obtener detalles de material
def material_detail_api(request, material_id):
    """
    API endpoint que devuelve los datos de un material en formato JSON.
    
    URL: /purchases/api/material/<material_id>/
    Método: GET
    Parámetro: material_id puede ser el ID numérico o el material_code
    
    Retorna:
        - 200: JSON con los datos del material
        - 404: Si el material no existe
    """
    try:
        # Intentar buscar por id_material primero (ej: MP-105)
        try:
            material = Material.objects.get(id_material=material_id)
        except Material.DoesNotExist:
            # Si falla, intentar por ID numérico (PK)
            material = Material.objects.get(id=int(material_id))
        
        data = {
            'material_id': material.id,
            'id_material': material.id_material,
            'name': material.name,
            'description': material.description,
            'material_code': material.id_material,
            'default_unit': material.unit.name if material.unit else None,
            'default_unit_id': material.unit.id if material.unit else None,
            'material_type': material.material_type.name if material.material_type else None,
            'status': material.status.name if material.status else None,
        }
        
        return JsonResponse(data)
    
    except (Material.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Material not found'}, status=404)

# API para crear pedido de compra (POST JSON)
@csrf_exempt
@transaction.atomic
def create_purchase_order_api(request):
    """
    API endpoint que crea una orden de compra con sus líneas.
    
    URL: /purchases/api/create/
    Método: POST
    Content-Type: application/json
    
    Espera un JSON con:
    {
        "supplier_id": <int>,
        "estimated_delivery_date": "YYYY-MM-DD",
        "lines": [
            {
                "material_id": <int>,
                "quantity": <int>,
                "unit_id": <int>,
                "price": <decimal>,
                "currency_id": <int>
            },
            ...
        ]
    }
    
    Retorna:
        - 200: {"message": "Purchase order created successfully", "purchase_order_id": <id>}
        - 400: {"error": "mensaje de error"}
        - 405: {"error": "Method not allowed"}
        - 500: {"error": "mensaje de error interno"}
    """
    
    # Validar método
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        # Parsear el JSON del body
        data = json.loads(request.body)
        
        # Validar presencia de campos requeridos
        supplier_id = data.get('supplier_id')
        estimated_delivery_date = data.get('estimated_delivery_date')
        lines = data.get('lines', [])
        
        if not supplier_id:
            return JsonResponse({'error': 'supplier_id is required'}, status=400)
        
        if not estimated_delivery_date:
            return JsonResponse({'error': 'estimated_delivery_date is required'}, status=400)
        
        if not lines or len(lines) == 0:
            return JsonResponse({'error': 'At least one line item is required'}, status=400)
        
        # Validar que el proveedor exista
        try:
            supplier = Supplier.objects.get(id=supplier_id)
        except Supplier.DoesNotExist:
            return JsonResponse({'error': f'Supplier with id {supplier_id} does not exist'}, status=400)
        
        # Obtener el estado por defecto (DRAFT)
        try:
            default_status = OrderStatus.objects.get(symbol='DRAFT')
        except OrderStatus.DoesNotExist:
            return JsonResponse({
                'error': 'Estado "DRAFT" no encontrado. Por favor, cree el estado DRAFT en el sistema.'
            }, status=400)
        
        # Generar el siguiente id_purchase_order
        # Buscar el último pedido y sumar 1
        last_order = PurchaseOrder.objects.order_by('-id').first()
        if last_order and last_order.id_purchase_order:
            # Extraer el número del último ID (ej: "PO-0001" -> 1)
            try:
                last_number = int(last_order.id_purchase_order.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                next_number = 1
        else:
            next_number = 1
        
        new_purchase_order_id = f"PO-{next_number:04d}"
        
        # Crear el PurchaseOrder
        purchase_order = PurchaseOrder.objects.create(
            id_purchase_order=new_purchase_order_id,
            supplier=supplier,
            issue_date=date.today(),
            estimated_delivery_date=estimated_delivery_date,
            status=default_status,
            created_by=request.user if request.user.is_authenticated else None
        )
        
        # Validar y crear las líneas
        for index, line_data in enumerate(lines, start=1):
            material_id = line_data.get('material_id')
            quantity = line_data.get('quantity')
            unit_id = line_data.get('unit_id')
            price = line_data.get('price')
            currency_id = line_data.get('currency_id')
            
            # Validar campos requeridos
            if not material_id:
                return JsonResponse({'error': f'Line {index}: material_id is required'}, status=400)
            
            if not quantity or quantity <= 0:
                return JsonResponse({'error': f'Line {index}: quantity must be greater than 0'}, status=400)
            
            if not unit_id:
                return JsonResponse({'error': f'Line {index}: unit_id is required'}, status=400)
            
            if price is None or price < 0:
                return JsonResponse({'error': f'Line {index}: price must be 0 or greater'}, status=400)
            
            if not currency_id:
                return JsonResponse({'error': f'Line {index}: currency_id is required'}, status=400)
            
            # Validar que los objetos relacionados existan
            try:
                # Intentar buscar por id_material (código ERP como MP-105)
                try:
                    material = Material.objects.get(id_material=material_id)
                except Material.DoesNotExist:
                    # Si falla, intentar por PK numérico
                    material = Material.objects.get(id=int(material_id))
            except (Material.DoesNotExist, ValueError):
                return JsonResponse({'error': f'Line {index}: Material not found ({material_id})'}, status=400)
            
            try:
                unit = Unit.objects.get(id=unit_id)
            except Unit.DoesNotExist:
                return JsonResponse({'error': f'Line {index}: Unit with id {unit_id} does not exist'}, status=400)
            
            try:
                currency = Currency.objects.get(id=currency_id)
            except Currency.DoesNotExist:
                return JsonResponse({'error': f'Line {index}: Currency with id {currency_id} does not exist'}, status=400)
            
            # Generar id_purchase_order_line
            line_id = f"{new_purchase_order_id}-L{index:03d}"
            
            # Crear la línea del pedido
            PurchaseOrderLine.objects.create(
                id_purchase_order_line=line_id,
                purchase_order=purchase_order,
                material=material,
                position=index,
                quantity=quantity,
                unit_material=unit,
                price=price,
                currency_supplier=currency,
                received_quantity=0,
                created_by=request.user if request.user.is_authenticated else None
            )
        
        return JsonResponse({
            'message': 'Purchase order created successfully',
            'id_purchase_order': new_purchase_order_id,
            'purchase_order_id': new_purchase_order_id,
            'lines_created': len(lines)
        }, status=200)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    
    except Exception as e:
        # Log the error for debugging
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': f'Internal server error: {str(e)}'}, status=500)
