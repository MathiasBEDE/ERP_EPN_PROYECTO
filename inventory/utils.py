"""
Utility functions for inventory management.

This module provides helper functions for inventory operations including:
- Getting default inventory locations
- Creating inventory movements from purchase orders
- Managing stock transactions
"""

from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from inventory.models import InventoryLocation, MovementType, InventoryMovement


def get_default_inventory_location():
    """
    Get the default inventory location for receiving materials.
    
    Returns the location marked as main_location=True, or the first
    available location if no main location is defined.
    
    Returns:
        InventoryLocation: The default location to use for receipts.
        
    Raises:
        InventoryLocation.DoesNotExist: If no locations exist in the database.
    """
    # Try to get the main location first
    main_location = InventoryLocation.objects.filter(
        main_location=True, 
        status=True
    ).first()
    
    if main_location:
        return main_location
    
    # If no main location, get the first active location
    first_location = InventoryLocation.objects.filter(status=True).first()
    
    if first_location:
        return first_location
    
    # If still no location, raise exception
    raise InventoryLocation.DoesNotExist(
        "No hay ubicaciones de inventario activas en el sistema. "
        "Por favor, cree al menos una ubicación."
    )


def create_inventory_movements_for_purchase_order(purchase_order, user=None):
    """
    Create inventory movements for a purchase order that has been fully received.
    
    This function creates an entry (PURCHASE_IN) movement for each line in the
    purchase order. It uses the received_quantity if available, otherwise uses
    the original quantity.
    
    To avoid duplicates, this function checks if movements already exist for
    this purchase order reference before creating new ones.
    
    Args:
        purchase_order: PurchaseOrder instance that has been received.
        user: User instance who is performing the action (optional).
        
    Returns:
        list: List of created InventoryMovement instances.
        
    Raises:
        InventoryLocation.DoesNotExist: If no default location is found.
        MovementType.DoesNotExist: If PURCHASE_IN movement type doesn't exist.
    """
    
    # Use destination_location if specified, otherwise use default location
    if purchase_order.destination_location:
        location = purchase_order.destination_location
    else:
        location = get_default_inventory_location()
    
    # Get the PURCHASE_IN movement type
    try:
        movement_type = MovementType.objects.get(symbol='PURCHASE_IN')
    except MovementType.DoesNotExist:
        raise MovementType.DoesNotExist(
            "Tipo de movimiento 'PURCHASE_IN' no encontrado. "
            "Por favor, ejecute el comando init_movement_types."
        )
    
    # Check if movements already exist for this purchase order
    # to avoid duplicates
    existing_movements = InventoryMovement.objects.filter(
        reference=purchase_order.id_purchase_order,
        movement_type=movement_type
    ).exists()
    
    if existing_movements:
        # Movements already exist, don't create duplicates
        return []
    
    created_movements = []
    
    # Iterate through all lines and create movements
    for line in purchase_order.lines.all():
        # Use received_quantity if > 0, otherwise use the original quantity
        quantity_to_receive = line.received_quantity if line.received_quantity > 0 else line.quantity
        
        # Skip lines with zero quantity
        if quantity_to_receive <= 0:
            continue
        
        # Generate unique ID for the movement
        # Format: INV-YYYYMMDD-HHMMSS-LINE_ID
        timestamp = timezone.now().strftime('%Y%m%d-%H%M%S')
        movement_id = f"INV-{timestamp}-{line.id}"
        
        # Create the inventory movement
        movement = InventoryMovement(
            id_inventory_movement=movement_id,
            location=location,
            material=line.material,
            quantity=quantity_to_receive,
            unit_type=line.unit_material,
            movement_type=movement_type,
            movement_date=timezone.now(),
            reference=purchase_order.id_purchase_order,
            created_by=user
        )
        
        # Validar integridad antes de guardar
        try:
            movement.full_clean()
            movement.save()
            created_movements.append(movement)
        except ValidationError as e:
            # Si hay un error de validación en movimientos automáticos,
            # registrar el error pero continuar con los demás
            # En producción, podría loggearse o manejarse de otra forma
            print(f"Error al crear movimiento para línea {line.id}: {e}")
            continue
    
    return created_movements


def create_inventory_movements_for_production_order(production_order, user=None):
    """
    Create inventory movements for a production order (work order) that has been completed.
    
    This function creates:
    1. Output movements (PRODUCTION_OUT) for each component consumed from origin_location
    2. Input movement (PRODUCTION_IN) for the finished product into destination_location
    
    To avoid duplicates, this function checks if movements already exist for
    this production order reference before creating new ones.
    
    Args:
        production_order: WorkOrder instance that has been completed.
        user: User instance who is performing the action (optional).
        
    Returns:
        list: List of created InventoryMovement instances.
        
    Raises:
        InventoryLocation.DoesNotExist: If origin or destination location is not set.
        MovementType.DoesNotExist: If PRODUCTION_IN/OUT movement types don't exist.
    """
    
    # Validar que las ubicaciones estén definidas
    if not production_order.origin_location:
        raise ValueError(
            "origin_location no está definido en la orden de producción. "
            "Se requiere una ubicación de origen para descontar componentes."
        )
    
    if not production_order.destination_location:
        raise ValueError(
            "destination_location no está definido en la orden de producción. "
            "Se requiere una ubicación de destino para el producto terminado."
        )
    
    # Get or create the PRODUCTION_OUT movement type
    try:
        mt_out = MovementType.objects.get(symbol='PRODUCTION_OUT')
    except MovementType.DoesNotExist:
        mt_out = MovementType.objects.create(
            name='Consumo en Producción',
            symbol='PRODUCTION_OUT'
        )
    
    # Get or create the PRODUCTION_IN movement type
    try:
        mt_in = MovementType.objects.get(symbol='PRODUCTION_IN')
    except MovementType.DoesNotExist:
        mt_in = MovementType.objects.create(
            name='Producto Terminado',
            symbol='PRODUCTION_IN'
        )
    
    # Check if movements already exist for this production order to avoid duplicates
    existing_movements = InventoryMovement.objects.filter(
        reference=production_order.id_work_order
    ).exists()
    
    if existing_movements:
        # Movements already exist, don't create duplicates
        return []
    
    created_movements = []
    
    # Use transaction to ensure atomicity
    with transaction.atomic():
        timestamp = timezone.now().strftime('%Y%m%d-%H%M%S')
        
        # Create output movements for each component (PRODUCTION_OUT)
        for line in production_order.bill_of_materials.lines.all():
            quantity_consumed = line.quantity * production_order.quantity
            
            # Skip lines with zero quantity
            if quantity_consumed <= 0:
                continue
            
            # Generate unique ID for the movement
            movement_id = f"INV-{timestamp}-OUT-{line.id}"
            
            # Create the inventory movement for component consumption
            movement = InventoryMovement(
                id_inventory_movement=movement_id,
                location=production_order.origin_location,
                material=line.component,
                quantity=quantity_consumed,
                unit_type=line.unit_component,
                movement_type=mt_out,
                movement_date=timezone.now(),
                reference=production_order.id_work_order,
                created_by=user
            )
            
            # Validar integridad antes de guardar
            try:
                movement.full_clean()
                movement.save()
                created_movements.append(movement)
            except ValidationError as e:
                # Si hay un error de validación, propagar la excepción
                # para que la transacción haga rollback
                raise ValidationError(
                    f"Error al crear movimiento de salida para componente {line.component.name}: {e}"
                )
        
        # Create input movement for finished product (PRODUCTION_IN)
        product = production_order.bill_of_materials.material
        movement_id = f"INV-{timestamp}-IN-WO{production_order.id}"
        
        movement = InventoryMovement(
            id_inventory_movement=movement_id,
            location=production_order.destination_location,
            material=product,
            quantity=production_order.quantity,
            unit_type=product.unit,
            movement_type=mt_in,
            movement_date=timezone.now(),
            reference=production_order.id_work_order,
            created_by=user
        )
        
        # Validar integridad antes de guardar
        try:
            movement.full_clean()
            movement.save()
            created_movements.append(movement)
        except ValidationError as e:
            # Si hay un error de validación, propagar la excepción
            raise ValidationError(
                f"Error al crear movimiento de entrada para producto {product.name}: {e}"
            )
    
    return created_movements


def create_inventory_movements_for_sales_order(sales_order, user=None):
    """
    Create inventory movements for a sales order that has been delivered.
    
    This function creates an output (SALE_OUT) movement for each line in the
    sales order. It deducts the quantities from the source location specified
    in the order, or from the default location if not specified.
    
    To avoid duplicates, this function checks if movements already exist for
    this sales order reference before creating new ones.
    
    Args:
        sales_order: SalesOrder instance that has been delivered.
        user: User instance who is performing the action (optional).
        
    Returns:
        list: List of created InventoryMovement instances.
        
    Raises:
        InventoryLocation.DoesNotExist: If no source location is found.
        MovementType.DoesNotExist: If SALE_OUT movement type doesn't exist.
        ValidationError: If there is insufficient stock for the delivery.
    """
    
    # Use source_location if specified, otherwise use default location
    if sales_order.source_location:
        location = sales_order.source_location
    else:
        location = get_default_inventory_location()
    
    # Get the SALE_OUT movement type
    try:
        movement_type = MovementType.objects.get(symbol='SALE_OUT')
    except MovementType.DoesNotExist:
        raise MovementType.DoesNotExist(
            "Tipo de movimiento 'SALE_OUT' no encontrado. "
            "Por favor, ejecute el comando init_movement_types."
        )
    
    # Check if movements already exist for this sales order
    # to avoid duplicates
    existing_movements = InventoryMovement.objects.filter(
        reference=sales_order.id_sales_order,
        movement_type=movement_type
    ).exists()
    
    if existing_movements:
        # Movements already exist, don't create duplicates
        return []
    
    created_movements = []
    
    # Iterate through all lines and create movements
    for line in sales_order.lines.all():
        # Use the quantity from the line (assuming full delivery)
        # In the future, you could use delivered_quantity for partial deliveries
        quantity_to_deliver = line.quantity
        
        # Skip lines with zero quantity
        if quantity_to_deliver <= 0:
            continue
        
        # Generate unique ID for the movement
        # Format: INV-YYYYMMDD-HHMMSS-LINE_ID
        timestamp = timezone.now().strftime('%Y%m%d-%H%M%S')
        movement_id = f"INV-{timestamp}-{line.id}"
        
        # Create the inventory movement
        movement = InventoryMovement(
            id_inventory_movement=movement_id,
            location=location,
            material=line.material,
            quantity=quantity_to_deliver,
            unit_type=line.unit_material,
            movement_type=movement_type,
            movement_date=timezone.now(),
            reference=sales_order.id_sales_order,
            created_by=user
        )
        
        # Validate integrity before saving
        # This will check if there is sufficient stock for the output movement
        try:
            movement.full_clean()
            movement.save()
            created_movements.append(movement)
        except ValidationError as e:
            # For sales orders, if there's insufficient stock, we should abort
            # the entire delivery operation to maintain consistency
            raise ValidationError(
                f"Stock insuficiente para entregar {line.material.name} "
                f"(línea {line.position}): {e}"
            )
    
    return created_movements

