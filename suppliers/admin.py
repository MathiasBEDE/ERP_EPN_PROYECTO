from django.contrib import admin
from .models import Supplier, PaymentMethod

# Register your models here.

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['id_supplier', 'name', 'country', 'category', 'status']
    list_filter = ['country', 'category', 'status']
    search_fields = ['id_supplier', 'name', 'legal_name', 'email']
