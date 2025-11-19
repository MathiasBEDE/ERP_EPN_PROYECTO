from materials.models import Material
from django.db.models import Q

print('=== VERIFICANDO FILTRO CORREGIDO (sin symbol) ===')
active_with_unit = Material.objects.filter(
    unit__isnull=False
).filter(
    Q(status__name='Activo') | Q(status__name='Active')
).select_related('unit', 'status')

print(f'Total materiales activos con unidad: {active_with_unit.count()}')
print('\nMateriales encontrados:')
for m in active_with_unit:
    print(f'  {m.id_material} - {m.name}')
    print(f'    Unit: {m.unit.symbol} ({m.unit.name})')
    print(f'    Status: {m.status.name}')
