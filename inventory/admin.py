from django.contrib import admin
from .models import MovementType, InventoryLocation, InventoryMovement

@admin.register(MovementType)
class MovementTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol', 'created_by']
    search_fields = ['name', 'symbol']
    fields = ['name', 'symbol', 'created_by']

@admin.register(InventoryLocation)
class InventoryLocationAdmin(admin.ModelAdmin):
    list_display = ['id_location', 'name', 'code', 'main_location', 'status']
    list_filter = ['main_location', 'status']
    search_fields = ['name', 'code', 'location']

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ['id_inventory_movement', 'location', 'material', 'quantity', 'unit_type', 'movement_type', 'created_at']
    list_filter = ['location', 'movement_type', 'created_at']
