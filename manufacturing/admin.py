from django.contrib import admin
from manufacturing.models import WorkOrderStatus, WorkOrder, BillOfMaterials, BillOfMaterialsLine


# Admin para líneas de BOM como inline
class BillOfMaterialsLineInline(admin.TabularInline):
    model = BillOfMaterialsLine
    extra = 1


# Admin para Bill of Materials con líneas inline
@admin.register(BillOfMaterials)
class BillOfMaterialsAdmin(admin.ModelAdmin):
    list_display = ('id_bill_of_materials', 'material')
    search_fields = ('id_bill_of_materials', 'material__name')
    inlines = [BillOfMaterialsLineInline]


# Admin para órdenes de producción
@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('id_work_order', 'bill_of_materials', 'quantity', 'status', 'created_at')
    search_fields = ('id_work_order', 'bill_of_materials__material__name')
    list_filter = ('status__name',)
    readonly_fields = ('created_at', 'updated_at')


# Admin para estados de orden de producción
@admin.register(WorkOrderStatus)
class WorkOrderStatusAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'created_at')
    search_fields = ('name', 'symbol')

