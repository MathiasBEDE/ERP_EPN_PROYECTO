from django.contrib import admin
from .models import ReportSnapshot


@admin.register(ReportSnapshot)
class ReportSnapshotAdmin(admin.ModelAdmin):
    list_display = [
        'id_snapshot',
        'report_type',
        'period_start',
        'period_end',
        'total_income',
        'total_expenses',
        'net_profit',
        'created_at'
    ]
    list_filter = ['report_type', 'period_start', 'period_end']
    search_fields = ['id_snapshot', 'report_type']
    readonly_fields = ['created_at', 'created_by']
    
    fieldsets = (
        ('Información del Reporte', {
            'fields': ('id_snapshot', 'report_type', 'period_start', 'period_end')
        }),
        ('Métricas Financieras', {
            'fields': ('total_income', 'total_expenses', 'net_profit')
        }),
        ('Métricas Operacionales', {
            'fields': ('total_sales', 'total_purchases', 'total_production_orders', 'inventory_value')
        }),
        ('Datos Adicionales', {
            'fields': ('additional_data',),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es nuevo
            obj.created_by = request.user
            if not obj.id_snapshot:
                obj.id_snapshot = ReportSnapshot.generate_snapshot_id()
        super().save_model(request, obj, form, change)
