from django.db import models
from django.db.models import Sum, F
from users.models import User
from suppliers.models import Supplier
from materials.models import Material, Unit
from accounting.models import Currency

class OrderStatus(models.Model):
    name = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "order_status"
        verbose_name = "Order Status"
        verbose_name_plural = "Order Statuses"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"

class PurchaseOrder(models.Model):
    id_purchase_order = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    issue_date = models.DateField()
    estimated_delivery_date = models.DateField()
    status = models.ForeignKey(OrderStatus, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "purchase_order"
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.id_purchase_order} - {self.supplier.name}"
    
    def get_total_amount(self):
        """
        Calcula el monto total de la orden sumando precio * cantidad de todas las líneas.
        
        Returns:
            Decimal: Total de la orden o 0 si no hay líneas
        """
        total = self.lines.aggregate(
            total=Sum(F('price') * F('quantity'), output_field=models.DecimalField())
        )['total']
        return total if total is not None else 0

class PurchaseOrderLine(models.Model):
    id_purchase_order_line = models.CharField(max_length=50, unique=True)
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='lines')
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    position = models.IntegerField()
    quantity = models.IntegerField()
    unit_material = models.ForeignKey(Unit, on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency_supplier = models.ForeignKey(Currency, on_delete=models.PROTECT)
    received_quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "lines_purchase_order"
        verbose_name = "Purchase Order Line"
        verbose_name_plural = "Purchase Order Lines"
        ordering = ['purchase_order', 'position']
    
    def __str__(self):
        return f"{self.id_purchase_order_line} - {self.material.name}"
