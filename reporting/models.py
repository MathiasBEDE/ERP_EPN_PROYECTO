from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class ReportSnapshot(models.Model):
    """
    Modelo para guardar instantáneas de reportes mensuales.
    Permite mantener un historial de métricas clave del ERP.
    """
    REPORT_TYPE_CHOICES = [
        ('MONTHLY_SUMMARY', 'Resumen Mensual'),
        ('SALES_REPORT', 'Reporte de Ventas'),
        ('PURCHASE_REPORT', 'Reporte de Compras'),
        ('INVENTORY_REPORT', 'Reporte de Inventario'),
        ('PRODUCTION_REPORT', 'Reporte de Producción'),
        ('ACCOUNTING_REPORT', 'Reporte Contable'),
    ]
    
    id_snapshot = models.CharField(max_length=50, unique=True, primary_key=True)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPE_CHOICES)
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Métricas financieras
    total_income = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Métricas operacionales
    total_sales = models.IntegerField(default=0)
    total_purchases = models.IntegerField(default=0)
    total_production_orders = models.IntegerField(default=0)
    
    # Valor de inventario
    inventory_value = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Datos adicionales en JSON
    additional_data = models.JSONField(default=dict, blank=True)
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = 'report_snapshot'
        verbose_name = 'Instantánea de Reporte'
        verbose_name_plural = 'Instantáneas de Reportes'
        ordering = ['-period_end', '-created_at']
        indexes = [
            models.Index(fields=['report_type', 'period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.get_report_type_display()} - {self.period_start} al {self.period_end}"
    
    @classmethod
    def generate_snapshot_id(cls):
        """Genera un ID único para el snapshot"""
        import uuid
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        unique = str(uuid.uuid4())[:8]
        return f"SNAP-{timestamp}-{unique}"
