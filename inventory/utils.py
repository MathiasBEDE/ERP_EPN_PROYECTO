"""
Utility functions for inventory management.

This module provides helper functions for inventory operations including:
- Getting default inventory locations
- Creating inventory movements from purchase orders
- Managing stock transactions
"""

from django.utils import timezone
from django.db import transaction
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
    
    # Get the default location
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
        movement = InventoryMovement.objects.create(
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
        
        created_movements.append(movement)
    
    return created_movements
