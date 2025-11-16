from django.contrib import admin
from .models import Material, Unit, MaterialType

# Register your models here.

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol']

@admin.register(MaterialType)
class MaterialTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol']

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['id_material', 'name', 'unit', 'material_type', 'status']
    list_filter = ['material_type', 'status']
    search_fields = ['id_material', 'name', 'description']
