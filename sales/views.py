from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from customers.models import Customer
from materials.models import Material, Unit
from core.models import Currency
from purchases.models import OrderStatus
from inventory.models import InventoryLocation, MovementType
from inventory.utils import create_inventory_movements_for_sales_order
from accounting.utils import create_entry_for_sale
from .models import SalesOrder, SalesOrderLine
from datetime import date
import json
import logging
import csv

# Configure logger
logger = logging.getLogger(__name__)


def sales_order_list_view(request):
    """
    Vista que muestra la lista paginada de órdenes de venta con filtros.
    
    URL: /sales/sales-order/
    Método: GET
    
    Parámetros GET opcionales:
        - q: Búsqueda por ID de orden o nombre de cliente
        - customer: Filtro por ID de cliente
        - status: Filtro por estado de orden
        - date_from: Fecha de inicio (filtro por issue_date)
        - date_to: Fecha de fin (filtro por issue_date)
        - export: Si es 'csv', exporta los resultados a CSV
        
    Retorna:
        - HTML con la lista de órdenes de venta
        - CSV si export=csv
    """
    
    # Obtener órdenes con relaciones optimizadas
    sales_orders = SalesOrder.objects.select_related(
        'customer', 
        'status', 
        'created_by',
        'source_location'
    ).all()
    
    # Aplicar filtros
    search_query = request.GET.get('q', '').strip()
    if search_query:
        sales_orders = sales_orders.filter(
            Q(id_sales_order__icontains=search_query) |
            Q(customer__name__icontains=search_query) |
            Q(customer__id_customer__icontains=search_query)
        )
    
    # Filtro por cliente
    customer_filter = request.GET.get('customer', '').strip()
    if customer_filter:
        sales_orders = sales_orders.filter(
            Q(customer__id_customer=customer_filter) |
            Q(customer__pk=customer_filter)
        )
    
    # Filtro por estado
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        sales_orders = sales_orders.filter(status__pk=status_filter)
    
    # Filtro por rango de fechas
    date_from = request.GET.get('date_from', '').strip()
    if date_from:
        try:
            sales_orders = sales_orders.filter(issue_date__gte=date_from)
        except ValueError:
            pass
    
    date_to = request.GET.get('date_to', '').strip()
    if date_to:
        try:
            sales_orders = sales_orders.filter(issue_date__lte=date_to)
        except ValueError:
            pass
    
    # Ordenar por fecha de creación (más recientes primero)
    sales_orders = sales_orders.order_by('-created_at')
    
    # Exportar a CSV si se solicita
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sales_orders.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['ID Orden', 'Cliente', 'ID Cliente', 'Fecha Emisión', 
                        'Estado', 'Ubicación Origen', 'Creado Por', 'Fecha Creación'])
        
        for order in sales_orders:
            writer.writerow([
                order.id_sales_order,
                order.customer.name,
                order.customer.id_customer,
                order.issue_date.strftime('%Y-%m-%d'),
                order.status.name,
                order.source_location.code if order.source_location else 'N/A',
                order.created_by.username if order.created_by else 'Sistema',
                order.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    
    # Paginación
    paginator = Paginator(sales_orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener datos para filtros
    statuses = OrderStatus.objects.all()
    customers = Customer.objects.filter(status=True).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'sales_orders': page_obj.object_list,
        'statuses': statuses,
        'customers': customers,
        'search_query': search_query,
        'customer_filter': customer_filter,
        'status_filter': status_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'sales/sales_order_list.html', context)


def sales_order_create_view(request):
    """
    Vista que muestra el formulario para crear una nueva orden de venta.
    
    URL: /sales/sales-order/new/
    Método: GET
    
    Retorna:
        - HTML con el formulario de creación de orden de venta
    """
    
    # Obtener datos necesarios para el formulario
    customers = Customer.objects.filter(status=True).order_by('name')
    currencies = Currency.objects.all().order_by('code')
    locations = InventoryLocation.objects.filter(status=True).order_by('code')
    materials = Material.objects.filter(status__name__in=['Activo', 'Active']).order_by('id_material')
    units = Unit.objects.all().order_by('symbol')
    today = date.today()
    
    context = {
        'customers': customers,
        'currencies': currencies,
        'locations': locations,
        'materials': materials,
        'units': units,
        'today': today,
    }
    
    return render(request, 'sales/sales_order_create.html', context)


def sales_order_edit_view(request, order_id):
    """
    Vista que muestra el formulario para editar una orden de venta existente.
    Solo permite editar órdenes en estado DRAFT.
    
    URL: /sales/sales-order/<order_id>/edit/
    Método: GET
    
    Retorna:
        - HTML con el formulario de edición de orden de venta
        - 404 si la orden no existe
        - Redirección con error si la orden no está en DRAFT
    """
    
    try:
        # Obtener la orden con sus relaciones
        order = SalesOrder.objects.select_related(
            'customer', 
            'status',
            'source_location'
        ).prefetch_related(
            'lines__material',
            'lines__unit_material',
            'lines__currency_customer'
        ).get(id_sales_order=order_id)
        
        # Verificar que esté en estado DRAFT
        if order.status.symbol != 'DRAFT':
            messages.error(
                request,
                f'No se puede editar una orden en estado "{order.status.name}". '
                f'Solo órdenes en estado Draft pueden editarse.'
            )
            return redirect('sales:sales_order_detail', order_id=order.id_sales_order)
        
        # Obtener datos necesarios para el formulario
        currencies = Currency.objects.all().order_by('code')
        locations = InventoryLocation.objects.filter(status=True).order_by('code')
        
        context = {
            'order': order,
            'currencies': currencies,
            'locations': locations,
        }
        
        return render(request, 'sales/sales_order_edit.html', context)
        
    except SalesOrder.DoesNotExist:
        raise Http404("Orden de venta no encontrada")


def sales_order_detail_view(request, order_id):
    """
    Vista que muestra el detalle completo de una orden de venta.
    También maneja las acciones de cambio de estado (Confirmar, Entregar, Cancelar).
    
    URL: /sales/sales-order/<order_id>/
    Método: GET, POST
    
    Acciones POST:
        - confirm: Confirma la orden (DRAFT -> CONFIRMED)
        - deliver: Marca la orden como entregada (CONFIRMED -> DELIVERED)
        - cancel: Cancela la orden
    
    Retorna:
        - HTML con el detalle de la orden de venta
        - 404 si la orden no existe
    """
    
    # Mapeo de acciones a símbolos de estado
    ACTION_STATUS_MAP = {
        "confirm": "CONFIRMED",
        "deliver": "DELIVERED",
        "cancel": "CANCELLED"
    }
    
    try:
        # Obtener la orden con todas sus relaciones optimizadas
        order = SalesOrder.objects.select_related(
            'customer',
            'status',
            'created_by',
            'source_location'
        ).prefetch_related(
            'lines__material',
            'lines__unit_material',
            'lines__currency_customer'
        ).get(id_sales_order=order_id)
        
        # Manejar acciones POST
        if request.method == 'POST':
            action = request.POST.get('action')
            
            # Validar que la acción sea válida
            status_symbol = ACTION_STATUS_MAP.get(action)
            if not status_symbol:
                messages.error(request, 'Acción no válida.')
                return redirect('sales:sales_order_detail', order_id=order.id_sales_order)
            
            # Obtener el estado destino
            try:
                new_status = OrderStatus.objects.get(symbol=status_symbol)
            except OrderStatus.DoesNotExist:
                messages.error(
                    request,
                    f'Estado "{status_symbol}" no encontrado en el sistema.'
                )
                return redirect('sales:sales_order_detail', order_id=order.id_sales_order)
            
            # Aplicar lógica específica por acción
            if action == 'confirm':
                # Solo permitir confirmar si está en DRAFT
                if order.status.symbol != 'DRAFT':
                    messages.error(
                        request,
                        f'No se puede confirmar una orden en estado "{order.status.name}". '
                        f'Debe estar en estado Draft.'
                    )
                    return redirect('sales:sales_order_detail', order_id=order.id_sales_order)
                
                # Cambiar estado a CONFIRMED
                try:
                    with transaction.atomic():
                        order.status = new_status
                        order.save()
                        
                        messages.success(
                            request,
                            f'Orden {order.id_sales_order} confirmada exitosamente.'
                        )
                except Exception as e:
                    logger.error(f'Error al confirmar orden {order.id_sales_order}: {str(e)}')
                    messages.error(request, f'Error al confirmar la orden: {str(e)}')
                
                return redirect('sales:sales_order_detail', order_id=order.id_sales_order)
            
            elif action == 'deliver':
                # Solo permitir entregar si está en CONFIRMED
                if order.status.symbol != 'CONFIRMED':
                    messages.error(
                        request,
                        f'No se puede entregar una orden en estado "{order.status.name}". '
                        f'Debe estar en estado Confirmed.'
                    )
                    return redirect('sales:sales_order_detail', order_id=order.id_sales_order)
                
                # Implementar creación de movimientos de inventario
                try:
                    with transaction.atomic():
                        # Crear movimientos de inventario para la orden de venta
                        try:
                            created_movements = create_inventory_movements_for_sales_order(
                                order, 
                                user=request.user if request.user.is_authenticated else None
                            )
                        except InventoryLocation.DoesNotExist:
                            messages.error(
                                request,
                                'No hay ubicaciones de inventario configuradas. '
                                'Por favor, configure al menos una ubicación antes de entregar órdenes.'
                            )
                            return redirect('sales:sales_order_detail', order_id=order.id_sales_order)
                        except MovementType.DoesNotExist:
                            messages.error(
                                request,
                                'Tipo de movimiento SALE_OUT no encontrado. '
                                'Por favor, ejecute el comando: python manage.py init_movement_types'
                            )
                            return redirect('sales:sales_order_detail', order_id=order.id_sales_order)
                        except ValidationError as e:
                            messages.error(
                                request,
                                f'Error al actualizar inventario: {str(e)}'
                            )
                            return redirect('sales:sales_order_detail', order_id=order.id_sales_order)
                        
                        # Marcar todas las líneas como entregadas
                        for line in order.lines.all():
                            line.delivered_quantity = line.quantity
                            line.save()
                        
                        # Cambiar estado a DELIVERED
                        order.status = new_status
                        order.save()
                        
                        # Crear asiento contable automático
                        print(f"\nDEBUG VIEWS: Llamando create_entry_for_sale para orden {order.id_sales_order}")
                        try:
                            journal_entry = create_entry_for_sale(
                                order,
                                user=request.user if request.user.is_authenticated else None
                            )
                            if journal_entry:
                                print(f"DEBUG VIEWS: ✓ Asiento {journal_entry.id_journal_entry} creado exitosamente")
                                logger.info(f'Asiento contable {journal_entry.id_journal_entry} creado para venta {order.id_sales_order}')
                                messages.success(
                                    request, 
                                    f'Asiento contable {journal_entry.id_journal_entry} generado automáticamente.'
                                )
                            else:
                                print(f"DEBUG VIEWS: create_entry_for_sale retornó None (asiento ya existía)")
                        except ValidationError as e:
                            # Error de validación (ej: cuentas no configuradas) - MOSTRAR AL USUARIO
                            print(f"DEBUG VIEWS ERROR: ValidationError en contabilidad: {str(e)}")
                            logger.error(f'Error de validación al crear asiento contable para venta {order.id_sales_order}: {str(e)}')
                            messages.warning(
                                request,
                                f'⚠️ ORDEN ENTREGADA pero fallo contable: {str(e)}'
                            )
                        except Exception as e:
                            # Otros errores - mostrar al usuario también
                            print(f"DEBUG VIEWS ERROR: Excepción en contabilidad: {type(e).__name__}: {str(e)}")
                            logger.error(f'Error al crear asiento contable para venta {order.id_sales_order}: {str(e)}')
                            messages.warning(
                                request,
                                f'⚠️ ORDEN ENTREGADA pero error en contabilidad: {str(e)}'
                            )
                        
                        # Mensaje de éxito con número de movimientos creados
                        movements_count = len(created_movements)
                        messages.success(
                            request,
                            f'Orden {order.id_sales_order} marcada como entregada exitosamente. '
                            f'Se {"creó" if movements_count == 1 else "crearon"} '
                            f'{movements_count} movimiento{"" if movements_count == 1 else "s"} de inventario.'
                        )
                except Exception as e:
                    logger.error(f'Error al entregar orden {order.id_sales_order}: {str(e)}')
                    messages.error(request, f'Error al entregar la orden: {str(e)}')
                
                return redirect('sales:sales_order_detail', order_id=order.id_sales_order)
            
            elif action == 'cancel':
                # Permitir cancelar si está en DRAFT o CONFIRMED
                if order.status.symbol not in ['DRAFT', 'CONFIRMED']:
                    messages.error(
                        request,
                        f'No se puede cancelar una orden en estado "{order.status.name}". '
                        f'Solo órdenes en Draft o Confirmed pueden cancelarse.'
                    )
                    return redirect('sales:sales_order_detail', order_id=order.id_sales_order)
                
                # Cambiar estado a CANCELLED
                try:
                    with transaction.atomic():
                        order.status = new_status
                        order.save()
                        
                        messages.success(
                            request,
                            f'Orden {order.id_sales_order} cancelada exitosamente.'
                        )
                except Exception as e:
                    logger.error(f'Error al cancelar orden {order.id_sales_order}: {str(e)}')
                    messages.error(request, f'Error al cancelar la orden: {str(e)}')
                
                return redirect('sales:sales_order_detail', order_id=order.id_sales_order)
        
        # Renderizar detalle de la orden
        context = {
            'order': order,
        }
        
        return render(request, 'sales/sales_order_detail.html', context)
        
    except SalesOrder.DoesNotExist:
        raise Http404("Orden de venta no encontrada")


# ==================== APIs ====================

def customer_detail_api(request, customer_id):
    """
    API que retorna los datos de un cliente en formato JSON.
    
    URL: /sales/api/customer/<customer_id>/
    Método: GET
    
    Parámetros:
        - customer_id: ID del cliente (id_customer o pk)
        
    Retorna:
        - JSON con los datos del cliente
        - 404 si el cliente no existe o está inactivo
    """
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Intentar buscar por id_customer primero, luego por pk
        try:
            customer = Customer.objects.get(id_customer=customer_id, status=True)
        except Customer.DoesNotExist:
            try:
                customer = Customer.objects.get(pk=customer_id, status=True)
            except Customer.DoesNotExist:
                return JsonResponse({'error': 'Cliente no encontrado o inactivo'}, status=404)
        
        # Preparar datos del cliente
        data = {
            'id': customer.pk,
            'id_customer': customer.id_customer,
            'name': customer.name,
            'legal_name': customer.legal_name or '',
            'address': customer.address or '',
            'city': customer.city or '',
            'state_province': customer.state_province or '',
            'country': customer.country or '',
            'phone': str(customer.phone) if customer.phone else '',
            'email': customer.email or '',
            'contact_name': customer.contact_name or '',
            'status': 'Active' if customer.status else 'Inactive',
        }
        
        return JsonResponse(data)
        
    except Customer.DoesNotExist:
        return JsonResponse({'error': 'Cliente no encontrado'}, status=404)
    except Exception as e:
        logger.error(f'Error en customer_detail_api: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


def material_detail_api(request, material_id):
    """
    API que retorna los datos de un material en formato JSON.
    
    URL: /sales/api/material/<material_id>/
    Método: GET
    
    Parámetros:
        - material_id: ID del material (id_material o pk)
        
    Retorna:
        - JSON con los datos del material
        - 404 si el material no existe
    """
    
    if request.method != 'GET':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Intentar buscar por id_material primero, luego por pk
        try:
            material = Material.objects.select_related('unit', 'status').get(id_material=material_id)
        except Material.DoesNotExist:
            material = Material.objects.select_related('unit', 'status').get(pk=material_id)
        
        # Preparar datos del material
        data = {
            'id': material.pk,
            'id_material': material.id_material,
            'name': material.name,
            'description': material.description or '',
            'unit': {
                'id': material.unit.pk,
                'name': material.unit.name,
                'symbol': material.unit.symbol
            } if material.unit else None,
            'status': material.status.name if material.status else '',
        }
        
        return JsonResponse(data)
        
    except Material.DoesNotExist:
        return JsonResponse({'error': 'Material no encontrado'}, status=404)
    except Exception as e:
        logger.error(f'Error en material_detail_api: {str(e)}')
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
def create_sales_order_api(request):
    """
    API para crear una nueva orden de venta vía POST JSON.
    
    URL: /sales/api/create/
    Método: POST
    
    JSON esperado:
    {
        "customer_id": <ID del cliente>,
        "source_location_id": <ID de ubicación (opcional)>,
        "notes": <Notas (opcional)>,
        "lines": [
            {
                "material_id": <ID material>,
                "quantity": <int>,
                "unit_id": <ID unidad>,
                "price": <decimal>,
                "currency_id": <ID moneda>
            },
            ...
        ]
    }
    
    Retorna:
        - JSON con el id_sales_order creado si éxito
        - JSON con error si falla
    """
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        # Parsear JSON del body
        data = json.loads(request.body)
        
        # Validar campos requeridos
        if 'customer_id' not in data:
            return JsonResponse({'error': 'El campo customer_id es requerido'}, status=400)
        
        if 'lines' not in data or not isinstance(data['lines'], list) or len(data['lines']) == 0:
            return JsonResponse({'error': 'Debe incluir al menos una línea de orden'}, status=400)
        
        # Validar que el cliente existe y está activo
        try:
            customer = Customer.objects.get(id_customer=data['customer_id'], status=True)
        except Customer.DoesNotExist:
            try:
                customer = Customer.objects.get(pk=data['customer_id'], status=True)
            except Customer.DoesNotExist:
                return JsonResponse({'error': f'Cliente "{data["customer_id"]}" no encontrado o inactivo'}, status=400)
        
        # Validar ubicación de origen si viene
        source_location = None
        if 'source_location_id' in data and data['source_location_id']:
            try:
                source_location = InventoryLocation.objects.get(pk=data['source_location_id'])
            except InventoryLocation.DoesNotExist:
                return JsonResponse({'error': f'Ubicación con ID {data["source_location_id"]} no encontrada'}, status=400)
        
        # Obtener estado DRAFT
        try:
            draft_status = OrderStatus.objects.get(symbol='DRAFT')
        except OrderStatus.DoesNotExist:
            return JsonResponse({'error': 'Estado DRAFT no encontrado en el sistema'}, status=500)
        
        # Generar nuevo código de orden (SO-0001, SO-0002, ...)
        last_order = SalesOrder.objects.all().order_by('-created_at').first()
        if last_order and last_order.id_sales_order.startswith('SO-'):
            try:
                last_number = int(last_order.id_sales_order.split('-')[1])
                new_number = last_number + 1
            except (ValueError, IndexError):
                new_number = 1
        else:
            new_number = 1
        
        new_order_id = f"SO-{new_number:04d}"
        
        # Crear la orden dentro de una transacción
        with transaction.atomic():
            # Crear SalesOrder
            sales_order = SalesOrder(
                id_sales_order=new_order_id,
                customer=customer,
                issue_date=date.today(),
                status=draft_status,
                source_location=source_location,
                notes=data.get('notes', ''),
                created_by=request.user if request.user.is_authenticated else None
            )
            sales_order.save()
            
            # Crear líneas de orden
            for idx, line_data in enumerate(data['lines'], start=1):
                # Validar campos requeridos de la línea
                required_fields = ['material_id', 'quantity', 'unit_id', 'price', 'currency_id']
                for field in required_fields:
                    if field not in line_data:
                        return JsonResponse({
                            'error': f'Línea {idx}: campo "{field}" es requerido'
                        }, status=400)
                
                # Validar cantidad positiva
                try:
                    quantity = int(line_data['quantity'])
                    if quantity <= 0:
                        return JsonResponse({
                            'error': f'Línea {idx}: la cantidad debe ser mayor a cero'
                        }, status=400)
                except (ValueError, TypeError):
                    return JsonResponse({
                        'error': f'Línea {idx}: cantidad inválida'
                    }, status=400)
                
                # Validar precio no negativo
                try:
                    price = float(line_data['price'])
                    if price < 0:
                        return JsonResponse({
                            'error': f'Línea {idx}: el precio no puede ser negativo'
                        }, status=400)
                except (ValueError, TypeError):
                    return JsonResponse({
                        'error': f'Línea {idx}: precio inválido'
                    }, status=400)
                
                # Validar que el material existe
                try:
                    material = Material.objects.get(pk=line_data['material_id'])
                except Material.DoesNotExist:
                    return JsonResponse({
                        'error': f'Línea {idx}: material con ID {line_data["material_id"]} no encontrado'
                    }, status=400)
                
                # Validar que la unidad existe
                try:
                    unit = Unit.objects.get(pk=line_data['unit_id'])
                except Unit.DoesNotExist:
                    return JsonResponse({
                        'error': f'Línea {idx}: unidad con ID {line_data["unit_id"]} no encontrada'
                    }, status=400)
                
                # Validar que la moneda existe
                try:
                    currency = Currency.objects.get(pk=line_data['currency_id'])
                except Currency.DoesNotExist:
                    return JsonResponse({
                        'error': f'Línea {idx}: moneda con ID {line_data["currency_id"]} no encontrada'
                    }, status=400)
                
                # Generar ID de línea (SO-0001-L001, SO-0001-L002, ...)
                line_id = f"{new_order_id}-L{idx:03d}"
                
                # Crear SalesOrderLine
                sales_order_line = SalesOrderLine(
                    id_sales_order_line=line_id,
                    sales_order=sales_order,
                    material=material,
                    position=idx,
                    quantity=quantity,
                    unit_material=unit,
                    price=price,
                    currency_customer=currency,
                    delivered_quantity=0,
                    created_by=request.user if request.user.is_authenticated else None
                )
                sales_order_line.save()
            
            # Retornar éxito
            return JsonResponse({
                'success': True,
                'message': f'Orden de venta {new_order_id} creada exitosamente',
                'id_sales_order': new_order_id
            })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        logger.error(f'Error en create_sales_order_api: {str(e)}')
        return JsonResponse({'error': f'Error interno: {str(e)}'}, status=500)

