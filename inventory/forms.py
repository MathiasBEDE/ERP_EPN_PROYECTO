from django import forms
from django.db import models as django_models
from .models import InventoryMovement, MovementType, InventoryLocation
from materials.models import Material


class InventoryAdjustmentForm(forms.ModelForm):
    """
    Formulario para registrar ajustes manuales de inventario.
    Permite crear movimientos de tipo Ajuste (entrada o salida).
    """
    
    class Meta:
        model = InventoryMovement
        fields = ['material', 'location', 'movement_type', 'quantity', 'unit_type', 'reference']
        widgets = {
            'material': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'unit_type': forms.HiddenInput(),  # Campo oculto, se asigna automáticamente
            'location': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'movement_type': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'min': '0.01',
                'step': '0.01'
            }),
            'reference': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500',
                'placeholder': 'Ejemplo: Inventario inicial, Corrección por conteo físico...'
            }),
        }
        labels = {
            'material': 'Material',
            'location': 'Ubicación',
            'movement_type': 'Tipo de Ajuste',
            'quantity': 'Cantidad',
            'reference': 'Referencia (opcional)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Limitar movement_type solo a ajustes (ADJUSTMENT_IN y ADJUSTMENT_OUT)
        self.fields['movement_type'].queryset = MovementType.objects.filter(
            symbol__in=['ADJUSTMENT_IN', 'ADJUSTMENT_OUT']
        ).order_by('name')
        
        # Limitar ubicaciones solo a las activas
        self.fields['location'].queryset = InventoryLocation.objects.filter(
            status=True
        ).order_by('name')
        
        # Filtrar materiales: activos y con unidad definida
        # Buscar por status.name='Activo' o 'Active'
        self.fields['material'].queryset = Material.objects.filter(
            unit__isnull=False
        ).filter(
            django_models.Q(status__name='Activo') | django_models.Q(status__name='Active')
        ).select_related('unit', 'status').order_by('name')
        
        # Hacer todos los campos requeridos excepto reference y unit_type
        self.fields['material'].required = True
        self.fields['location'].required = True
        self.fields['movement_type'].required = True
        self.fields['quantity'].required = True
        self.fields['reference'].required = False
        self.fields['unit_type'].required = False  # Se asigna automáticamente en la vista
    
    def clean_material(self):
        """
        Validar que el material tenga una unidad definida.
        """
        material = self.cleaned_data.get('material')
        if material and not material.unit:
            raise forms.ValidationError(
                f'El material "{material.name}" no tiene una unidad definida. '
                'Por favor, configure una unidad para este material antes de continuar.'
            )
        return material
    
    def clean_quantity(self):
        """
        Validar que la cantidad sea positiva (mayor a 0).
        """
        quantity = self.cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError('La cantidad debe ser mayor a 0.')
        return quantity
