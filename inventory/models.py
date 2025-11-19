from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Sum, F, Case, When, DecimalField
from users.models import User
from materials.models import Material, Unit

class MovementType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "movement_type"
        verbose_name = "Movement Type"
        verbose_name_plural = "Movement Types"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"

class InventoryLocation(models.Model):
    id_location = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    main_location = models.BooleanField(default=False)
    location = models.CharField(max_length=300)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "location_inventory"
        verbose_name = "Inventory Location"
        verbose_name_plural = "Inventory Locations"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class InventoryMovement(models.Model):
    id_inventory_movement = models.CharField(max_length=50, unique=True)
    location = models.ForeignKey(InventoryLocation, on_delete=models.PROTECT)
    material = models.ForeignKey(Material, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_type = models.ForeignKey(Unit, on_delete=models.PROTECT)
    movement_type = models.ForeignKey(MovementType, on_delete=models.PROTECT)
    movement_date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "inventory_movements"
        verbose_name = "Inventory Movement"
        verbose_name_plural = "Inventory Movements"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.id_inventory_movement} - {self.material.name}"
    
    def clean(self):
        """
        Validaciones de integridad para movimientos de inventario:
        1. Cantidad debe ser positiva (> 0)
        2. Unidad debe coincidir con la unidad del material
        3. Para salidas, debe haber stock suficiente
        """
        errors = {}
        
        # Validación 1: Cantidad positiva
        if self.quantity is None or self.quantity <= 0:
            errors['quantity'] = 'La cantidad debe ser un número positivo mayor a cero.'
        
        # Validación 2: Coherencia de unidad
        # Verificar si unit_type está asignado antes de validar
        if self.material:
            try:
                # Intentar acceder a unit_type - puede no estar asignado aún
                if self.unit_type and self.unit_type != self.material.unit:
                    errors['unit_type'] = 'La unidad seleccionada no coincide con la unidad base del material.'
            except:
                # Si unit_type no está asignado aún, se asignará automáticamente en la vista
                pass
        
        # Validación 3: Stock suficiente para salidas
        if self.movement_type and self.movement_type.symbol.endswith('_OUT'):
            if self.material and self.location and self.quantity:
                # Calcular stock actual en esta ubicación para este material
                # Excluir el movimiento actual si ya existe (en caso de edición)
                movements_query = InventoryMovement.objects.filter(
                    material=self.material,
                    location=self.location
                )
                
                # Si estamos editando un movimiento existente, excluirlo del cálculo
                if self.pk:
                    movements_query = movements_query.exclude(pk=self.pk)
                
                # Calcular stock: entradas (+) - salidas (-)
                current_stock = movements_query.aggregate(
                    total=Sum(
                        Case(
                            When(movement_type__symbol__endswith='_OUT', then=-F('quantity')),
                            default=F('quantity'),
                            output_field=DecimalField()
                        )
                    )
                )['total'] or 0
                
                # Verificar si hay suficiente stock para esta salida
                if self.quantity > current_stock:
                    errors['quantity'] = (
                        f'Stock insuficiente en {self.location.name}. '
                        f'Disponible: {current_stock} {self.unit_type.symbol if self.unit_type else ""}'
                    )
        
        # Si hay errores, lanzar ValidationError
        if errors:
            raise ValidationError(errors)

