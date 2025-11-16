from django.db import models
from users.models import User
from core.models import Status

class Unit(models.Model):
    name = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=20)
    
    class Meta:
        db_table = "units"
        verbose_name = "Unit"
        verbose_name_plural = "Units"
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"

class MaterialType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=20)
    
    class Meta:
        db_table = "material_types"
        verbose_name = "Material Type"
        verbose_name_plural = "Material Types"
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"

class Material(models.Model):
    id_material = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    unit = models.ForeignKey(Unit, on_delete=models.PROTECT, default=1)
    material_type = models.ForeignKey(MaterialType, on_delete=models.PROTECT, default=1)
    status = models.ForeignKey(Status, on_delete=models.PROTECT, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "materials"
        verbose_name = "Material"
        verbose_name_plural = "Materiales"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.id_material} - {self.name}"
