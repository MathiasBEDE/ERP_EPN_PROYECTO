from django.contrib import admin
from .models import OrderStatus, PurchaseOrder, PurchaseOrderLine

@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'symbol', 'created_at']
    search_fields = ['name', 'symbol']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['id_purchase_order', 'supplier', 'issue_date', 'estimated_delivery_date', 'status']
    list_filter = ['status', 'issue_date', 'estimated_delivery_date', 'supplier']
    search_fields = ['id_purchase_order']

@admin.register(PurchaseOrderLine)
class PurchaseOrderLineAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'position', 'material', 'quantity', 'unit_material', 'price', 'currency_supplier', 'received_quantity']
    list_filter = ['material', 'unit_material', 'currency_supplier']
