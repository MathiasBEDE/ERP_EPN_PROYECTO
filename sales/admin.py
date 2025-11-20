from django.contrib import admin
from .models import SalesOrder, SalesOrderLine


class SalesOrderLineInline(admin.TabularInline):
    model = SalesOrderLine
    extra = 1
    fields = ['id_sales_order_line', 'material', 'position', 'quantity', 
              'unit_material', 'price', 'currency_customer', 'delivered_quantity']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ['id_sales_order', 'customer', 'issue_date', 'status', 
                    'invoice_number', 'source_location', 'created_at']
    list_filter = ['status', 'issue_date', 'created_at']
    search_fields = ['id_sales_order', 'customer__name', 'invoice_number']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    inlines = [SalesOrderLineInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('id_sales_order', 'customer', 'issue_date', 'status')
        }),
        ('Location', {
            'fields': ('source_location',)
        }),
        ('Additional Information', {
            'fields': ('notes', 'invoice_number')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(SalesOrderLine)
class SalesOrderLineAdmin(admin.ModelAdmin):
    list_display = ['id_sales_order_line', 'sales_order', 'material', 'position',
                    'quantity', 'price', 'currency_customer', 'delivered_quantity']
    list_filter = ['sales_order__status', 'created_at']
    search_fields = ['id_sales_order_line', 'sales_order__id_sales_order', 
                     'material__name']
    readonly_fields = ['created_at', 'updated_at', 'created_by']
    
    fieldsets = (
        ('Line Information', {
            'fields': ('id_sales_order_line', 'sales_order', 'position')
        }),
        ('Product Details', {
            'fields': ('material', 'quantity', 'unit_material', 'delivered_quantity')
        }),
        ('Pricing', {
            'fields': ('price', 'currency_customer')
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
