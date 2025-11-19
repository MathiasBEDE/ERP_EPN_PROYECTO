from django.db import models
from users.models import User
from materials.models import Material, Unit
from inventory.models import InventoryLocation


class WorkOrderStatus(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "work_order_status"
        verbose_name = "Work Order Status"
        verbose_name_plural = "Work Order Statuses"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.symbol})"


class BillOfMaterials(models.Model):
    id_bill_of_materials = models.CharField(max_length=50, unique=True)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)  # Producto terminado
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "bill_of_materials"
        verbose_name = "Bill of Materials"
        verbose_name_plural = "Bills of Materials"
        ordering = ['material']

    def __str__(self):
        return f"BOM {self.id_bill_of_materials} - {self.material.name}"


class BillOfMaterialsLine(models.Model):
    bill_of_materials = models.ForeignKey(BillOfMaterials, on_delete=models.CASCADE, related_name='lines')
    component = models.ForeignKey(Material, on_delete=models.PROTECT)  # Material requerido
    quantity = models.IntegerField()  # Cantidad del componente
    unit_component = models.ForeignKey(Unit, on_delete=models.PROTECT)

    class Meta:
        db_table = "lines_bill_of_materials"
        verbose_name = "Bill of Materials Line"
        verbose_name_plural = "Bill of Materials Lines"
        ordering = ['bill_of_materials', 'component']

    def __str__(self):
        return f"{self.component.name} x{self.quantity}"


class WorkOrder(models.Model):
    id_work_order = models.CharField(max_length=50, unique=True)
    bill_of_materials = models.ForeignKey(BillOfMaterials, on_delete=models.PROTECT)
    quantity = models.IntegerField()  # Cantidad a producir
    status = models.ForeignKey(WorkOrderStatus, on_delete=models.PROTECT)
    origin_location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT, related_name='work_orders_origin', null=True, blank=True)
    destination_location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT, related_name='work_orders_destination', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "work_order"
        verbose_name = "Work Order"
        verbose_name_plural = "Work Orders"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.id_work_order} - {self.bill_of_materials.material.name}"

