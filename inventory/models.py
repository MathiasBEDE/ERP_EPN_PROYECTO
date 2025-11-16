from django.db import models
from users.models import User
from materials.models import Material, Unit

class MovementType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "movement_type"
        verbose_name = "Movement Type"
        verbose_name_plural = "Movement Types"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"

class InventoryLocation(models.Model):
    id_location = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    main_location = models.BooleanField(default=False)
    location = models.CharField(max_length=300)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "location_inventory"
        verbose_name = "Inventory Location"
        verbose_name_plural = "Inventory Locations"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class InventoryMovement(models.Model):
    id_inventory_movement = models.CharField(max_length=50, unique=True)
    location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_type = models.ForeignKey(Unit, on_delete=models.PROTECT)
    movement_type = models.ForeignKey(MovementType, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "inventory_movements"
        verbose_name = "Inventory Movement"
        verbose_name_plural = "Inventory Movements"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.id_inventory_movement} - {self.material.name}"
