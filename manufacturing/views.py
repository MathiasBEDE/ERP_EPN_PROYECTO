from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from manufacturing.models import WorkOrder, WorkOrderStatus, BillOfMaterials
from accounting.utils import create_entry_for_production


@login_required
def work_order_list_view(request):
    # Manejar acciones de cambio de estado (iniciar, terminar producción)
    if request.method == 'POST':
        action = request.POST.get('action')
        wo_id = request.POST.get('work_order_id')
        work_order = get_object_or_404(WorkOrder, id_work_order=wo_id)
        
        if action == 'start':
            # Cambiar de Borrador a En Proceso
            if work_order.status.symbol == 'DRAFT':
                try:
                    new_status = WorkOrderStatus.objects.get(symbol='IN_PROGRESS')
                except WorkOrderStatus.DoesNotExist:
                    new_status = WorkOrderStatus.objects.create(name='En Proceso', symbol='IN_PROGRESS')
                work_order.status = new_status
                work_order.save()
                messages.success(request, f"Orden {work_order.id_work_order} iniciada.")
            else:
                messages.error(request, "La orden no está en estado Borrador.")
        
        elif action == 'finish':
            # Intentar completar la producción (requiere estado En Proceso)
            if work_order.status.symbol != 'IN_PROGRESS':
                messages.error(request, "Solo se puede terminar una orden en proceso activo.")
            else:
                from inventory.models import InventoryMovement
                from inventory.utils import create_inventory_movements_for_production_order, get_default_inventory_location
                
                # Validar que las ubicaciones estén definidas (asignar por defecto si es necesario)
                if not work_order.origin_location or not work_order.destination_location:
                    try:
                        default_location = get_default_inventory_location()
                        if not work_order.origin_location:
                            work_order.origin_location = default_location
                        if not work_order.destination_location:
                            work_order.destination_location = default_location
                        work_order.save()
                    except Exception as e:
                        messages.error(request, f"No hay ubicación de inventario por defecto: {str(e)}")
                        return redirect('manufacturing:work_order_list')
                
                # Validar stock para cada material del BOM en la ubicación origen
                insufficient = None
                for line in work_order.bill_of_materials.lines.all():
                    # Stock disponible del componente en la ubicación origen
                    total_in = InventoryMovement.objects.filter(
                        material=line.component,
                        location=work_order.origin_location,
                        movement_type__symbol__endswith='_IN'
                    ).aggregate(total=Sum('quantity'))['total'] or 0
                    
                    total_out = InventoryMovement.objects.filter(
                        material=line.component,
                        location=work_order.origin_location,
                        movement_type__symbol__endswith='_OUT'
                    ).aggregate(total=Sum('quantity'))['total'] or 0
                    
                    available = total_in - total_out
                    required = line.quantity * work_order.quantity
                    
                    if required > available:
                        insufficient = f"{line.component.name}: requiere {required}, disponible {available} en {work_order.origin_location.name}"
                        break
                
                if insufficient:
                    messages.error(request, f"Stock insuficiente para terminar producción ({insufficient}).")
                else:
                    # Usar la función centralizada para crear movimientos
                    try:
                        created_movements = create_inventory_movements_for_production_order(
                            production_order=work_order,
                            user=request.user
                        )
                        
                        # Actualizar estado a Terminado
                        done_status, _ = WorkOrderStatus.objects.get_or_create(
                            symbol='DONE',
                            defaults={'name': 'Terminado'}
                        )
                        work_order.status = done_status
                        work_order.save()
                        
                        # Crear asiento contable automático
                        try:
                            journal_entry = create_entry_for_production(
                                work_order,
                                user=request.user if request.user.is_authenticated else None
                            )
                            if journal_entry:
                                logger.info(f'Asiento contable {journal_entry.id_journal_entry} creado para producción {work_order.id_work_order}')
                                messages.success(
                                    request,
                                    f'Asiento contable {journal_entry.id_journal_entry} generado automáticamente.'
                                )
                        except ValidationError as e:
                            logger.error(f'Error de validación al crear asiento contable para producción {work_order.id_work_order}: {str(e)}')
                            messages.warning(
                                request,
                                f'⚠️ ORDEN TERMINADA pero fallo contable: {str(e)}'
                            )
                        except Exception as e:
                            # No fallar la transacción si hay error en contabilidad
                            logger.error(f'Error al crear asiento contable para producción {work_order.id_work_order}: {str(e)}')
                            messages.warning(
                                request,
                                f'⚠️ ORDEN TERMINADA pero error en contabilidad: {str(e)}'
                            )
                        
                        messages.success(
                            request,
                            f"Orden {work_order.id_work_order} terminada. "
                            f"Se crearon {len(created_movements)} movimientos de inventario."
                        )
                    except ValueError as e:
                        messages.error(request, f"Error de configuración: {str(e)}")
                    except Exception as e:
                        messages.error(request, f"Error al crear movimientos de inventario: {str(e)}")
        
        elif action == 'cancel':
            # Anular una orden de producción
            from inventory.models import InventoryMovement, MovementType
            
            try:
                with transaction.atomic():
                    # Buscar movimientos de inventario relacionados con esta orden
                    production_movements = InventoryMovement.objects.filter(
                        reference=work_order.id_work_order
                    )
                    
                    movements_count = production_movements.count()
                    
                    if movements_count > 0:
                        # La orden tiene movimientos, eliminarlos
                        production_movements.delete()
                        messages.info(
                            request, 
                            f"Se eliminaron {movements_count} movimientos de inventario asociados."
                        )
                    
                    # Cambiar estado a CANCELLED
                    try:
                        cancelled_status = WorkOrderStatus.objects.get(symbol='CANCELLED')
                    except WorkOrderStatus.DoesNotExist:
                        cancelled_status = WorkOrderStatus.objects.create(
                            name='Cancelada',
                            symbol='CANCELLED'
                        )
                    
                    work_order.status = cancelled_status
                    work_order.save()
                    
                    messages.success(
                        request, 
                        f"Orden {work_order.id_work_order} cancelada exitosamente."
                    )
            except Exception as e:
                messages.error(request, f"Error al cancelar la orden: {str(e)}")
        
        return redirect('manufacturing:work_order_list')
    
    # Obtener órdenes separadas por estado para vista tipo tablero
    draft_orders = WorkOrder.objects.filter(status__symbol='DRAFT')
    in_progress_orders = WorkOrder.objects.filter(status__symbol='IN_PROGRESS')
    done_orders = WorkOrder.objects.filter(status__symbol='DONE')
    cancelled_orders = WorkOrder.objects.filter(status__symbol='CANCELLED')
    context = {
        'draft_orders': draft_orders,
        'in_progress_orders': in_progress_orders,
        'done_orders': done_orders,
        'cancelled_orders': cancelled_orders
    }
    return render(request, 'manufacturing/work_order_list.html', context)


@login_required
def work_order_form_view(request):
    # Vista para crear una nueva orden de producción
    if request.method == 'POST':
        bom_id = request.POST.get('bill_of_materials')
        qty = int(request.POST.get('quantity', 1))
        origin_location_id = request.POST.get('origin_location')
        destination_location_id = request.POST.get('destination_location')
        
        try:
            bom = BillOfMaterials.objects.get(id=bom_id)
        except BillOfMaterials.DoesNotExist:
            messages.error(request, "Debe seleccionar un Bill of Materials válido.")
            return redirect('manufacturing:work_order_new')
        
        # Validar ubicaciones
        from inventory.models import InventoryLocation
        origin_location = None
        destination_location = None
        
        if origin_location_id:
            try:
                origin_location = InventoryLocation.objects.get(id=origin_location_id)
            except InventoryLocation.DoesNotExist:
                messages.error(request, "Ubicación de origen no válida.")
                return redirect('manufacturing:work_order_new')
        
        if destination_location_id:
            try:
                destination_location = InventoryLocation.objects.get(id=destination_location_id)
            except InventoryLocation.DoesNotExist:
                messages.error(request, "Ubicación de destino no válida.")
                return redirect('manufacturing:work_order_new')
        
        # Asignar estado inicial Borrador
        try:
            draft_status = WorkOrderStatus.objects.get(symbol='DRAFT')
        except WorkOrderStatus.DoesNotExist:
            draft_status = WorkOrderStatus.objects.create(name='Borrador', symbol='DRAFT')
        # Generar ID único para la orden (WO-0001, WO-0002, ...)
        count = WorkOrder.objects.count() + 1
        new_id = f"WO-{count:04d}"
        # Crear la orden de producción
        WorkOrder.objects.create(
            id_work_order=new_id,
            bill_of_materials=bom,
            quantity=qty,
            status=draft_status,
            origin_location=origin_location,
            destination_location=destination_location,
            created_by=request.user if request.user.is_authenticated else None
        )
        messages.success(request, f"Orden de Producción {new_id} creada en estado Borrador.")
        return redirect('manufacturing:work_order_list')
    else:
        # Obtener todos los BOM disponibles y ubicaciones activas para mostrar en el formulario
        from inventory.models import InventoryLocation
        bom_list = BillOfMaterials.objects.all().order_by('material__name')
        locations = InventoryLocation.objects.filter(status=True).order_by('name')
        return render(request, 'manufacturing/work_order_form.html', {
            'bom_list': bom_list,
            'locations': locations
        })


@login_required
def work_order_detail_view(request, wo_id):
    # Vista de detalle (placeholder)
    work_order = get_object_or_404(WorkOrder, id_work_order=wo_id)
    context = {'work_order': work_order}
    return render(request, 'manufacturing/work_order_detail.html', context)

