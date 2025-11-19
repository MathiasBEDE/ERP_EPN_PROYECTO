from materials.models import Material
from inventory.models import InventoryLocation

print('=== MATERIALES ===')
mats = Material.objects.all()
print(f'Total materiales: {mats.count()}')
for m in mats[:10]:
    status_name = m.status.name if m.status else "None"
    unit_name = m.unit.name if m.unit else "None"
    print(f'  {m.id_material} - {m.name} - Status: {status_name} - Unit: {unit_name}')

print(f'\n=== MATERIALES ACTIVOS CON UNIDAD ===')
active = Material.objects.filter(status__name='Active', unit__isnull=False)
print(f'Total: {active.count()}')
for m in active[:10]:
    print(f'  {m.id_material} - {m.name} - Unit: {m.unit.symbol}')

print(f'\n=== UBICACIONES ACTIVAS ===')
locs = InventoryLocation.objects.filter(status=True)
print(f'Total: {locs.count()}')
for loc in locs[:10]:
    print(f'  {loc.id_location} - {loc.name}')
