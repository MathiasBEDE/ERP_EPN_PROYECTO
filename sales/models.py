from django.db import models
from django.conf import settings
from customers.models import Customer
from materials.models import Material, Unit
from core.models import Currency
from purchases.models import OrderStatus
from inventory.models import InventoryLocation


class SalesOrder(models.Model):
    """
    Modelo para representar una orden de venta.
    Registra las ventas realizadas a clientes con sus líneas de productos/materiales.
    """
    id_sales_order = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Sales Order ID",
        help_text="Identificador único de la orden de venta (ej: SO-0001)"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name='sales_orders',
        verbose_name="Customer",
        help_text="Cliente al que se le vende"
    )
    issue_date = models.DateField(
        verbose_name="Issue Date",
        help_text="Fecha de emisión de la orden de venta"
    )
    status = models.ForeignKey(
        OrderStatus,
        on_delete=models.PROTECT,
        related_name='sales_orders',
        verbose_name="Status",
        help_text="Estado actual de la orden de venta"
    )
    source_location = models.ForeignKey(
        InventoryLocation,
        on_delete=models.PROTECT,
        related_name='sales_orders',
        null=True,
        blank=True,
        verbose_name="Source Location",
        help_text="Ubicación de inventario desde donde se despacha la orden"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes",
        help_text="Notas o comentarios adicionales sobre la orden"
    )
    invoice_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Invoice Number",
        help_text="Número de factura o referencia contable asociada (integración contable)"
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sales_orders',
        verbose_name="Created By"
    )
    
    class Meta:
        db_table = 'sales_order'
        verbose_name = 'Sales Order'
        verbose_name_plural = 'Sales Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['id_sales_order']),
            models.Index(fields=['customer']),
            models.Index(fields=['status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.id_sales_order} - {self.customer.name}"
    
    def get_total_amount(self):
        """
        Calcula el monto total de la orden sumando todas sus líneas.
        Retorna un diccionario con totales por moneda.
        """
        from decimal import Decimal
        from collections import defaultdict
        
        totals = defaultdict(Decimal)
        for line in self.lines.all():
            line_total = line.quantity * line.price
            currency_code = line.currency_customer.code
            totals[currency_code] += line_total
        
        return dict(totals)
    
    def get_delivery_status(self):
        """
        Calcula el estado de entrega de la orden.
        Retorna: 'not_delivered', 'partially_delivered', 'fully_delivered'
        """
        lines = self.lines.all()
        if not lines:
            return 'not_delivered'
        
        total_ordered = sum(line.quantity for line in lines)
        total_delivered = sum(line.delivered_quantity for line in lines)
        
        if total_delivered == 0:
            return 'not_delivered'
        elif total_delivered < total_ordered:
            return 'partially_delivered'
        else:
            return 'fully_delivered'


class SalesOrderLine(models.Model):
    """
    Modelo para representar una línea de orden de venta.
    Cada línea contiene un material/producto con su cantidad, precio y moneda.
    """
    id_sales_order_line = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Sales Order Line ID",
        help_text="Identificador único de la línea (ej: SO-0001-L001)"
    )
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name="Sales Order",
        help_text="Orden de venta a la que pertenece esta línea"
    )
    material = models.ForeignKey(
        Material,
        on_delete=models.PROTECT,
        related_name='sales_order_lines',
        verbose_name="Material",
        help_text="Material o producto vendido"
    )
    position = models.IntegerField(
        verbose_name="Position",
        help_text="Número de posición o secuencia de la línea en la orden"
    )
    quantity = models.IntegerField(
        verbose_name="Quantity",
        help_text="Cantidad vendida del material"
    )
    unit_material = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name='sales_order_lines',
        verbose_name="Unit",
        help_text="Unidad de medida del material"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Unit Price",
        help_text="Precio unitario de venta"
    )
    currency_customer = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='sales_order_lines',
        verbose_name="Currency",
        help_text="Moneda del precio de venta"
    )
    delivered_quantity = models.IntegerField(
        default=0,
        verbose_name="Delivered Quantity",
        help_text="Cantidad ya entregada del material"
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sales_order_lines',
        verbose_name="Created By"
    )
    
    class Meta:
        db_table = 'lines_sales_order'
        verbose_name = 'Sales Order Line'
        verbose_name_plural = 'Sales Order Lines'
        ordering = ['sales_order', 'position']
        indexes = [
            models.Index(fields=['id_sales_order_line']),
            models.Index(fields=['sales_order']),
            models.Index(fields=['material']),
        ]
        unique_together = [['sales_order', 'position']]
    
    def __str__(self):
        return f"{self.id_sales_order_line} - {self.material.name}"
    
    def get_line_total(self):
        """
        Calcula el total de la línea (cantidad × precio).
        """
        from decimal import Decimal
        return Decimal(self.quantity) * self.price
    
    def get_pending_quantity(self):
        """
        Calcula la cantidad pendiente de entrega.
        """
        return max(0, self.quantity - self.delivered_quantity)
    
    def is_fully_delivered(self):
        """
        Verifica si la línea ha sido completamente entregada.
        """
        return self.delivered_quantity >= self.quantity
