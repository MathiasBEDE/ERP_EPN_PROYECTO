from django import forms
from .models import SalesOrder, SalesOrderLine
from customers.models import Customer
from materials.models import Material
from core.models import Currency
from inventory.models import InventoryLocation


class SalesOrderForm(forms.ModelForm):
    """
    Formulario para crear/editar órdenes de venta.
    Nota: Este formulario es principalmente de referencia, 
    la creación se maneja mediante API JSON.
    """
    
    class Meta:
        model = SalesOrder
        fields = ['customer', 'issue_date', 'source_location', 'notes']
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo clientes activos
        self.fields['customer'].queryset = Customer.objects.filter(status=True).order_by('name')
        # Filtrar solo ubicaciones activas
        self.fields['source_location'].queryset = InventoryLocation.objects.filter(status=True).order_by('code')


class SalesOrderLineForm(forms.ModelForm):
    """
    Formulario para crear/editar líneas de orden de venta.
    """
    
    class Meta:
        model = SalesOrderLine
        fields = ['material', 'quantity', 'unit_material', 'price', 'currency_customer']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': '1'}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }

