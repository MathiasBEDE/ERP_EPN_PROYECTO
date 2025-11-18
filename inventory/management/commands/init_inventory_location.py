"""
Management command to initialize a default inventory location.

Usage:
    python manage.py init_inventory_location

This command creates a default inventory location if none exists.
"""

from django.core.management.base import BaseCommand
from inventory.models import InventoryLocation


class Command(BaseCommand):
    help = 'Initialize default inventory location'

    def handle(self, *args, **options):
        """
        Create default InventoryLocation if none exist.
        """
        
        # Check if any location exists
        existing_locations = InventoryLocation.objects.count()
        
        if existing_locations > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'Inventory locations already exist ({existing_locations} location(s)).'
                )
            )
            
            # Check if there's a main location
            main_location = InventoryLocation.objects.filter(main_location=True).first()
            if main_location:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Main location: {main_location.code} - {main_location.name}'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        'No main location is defined. Consider setting one.'
                    )
                )
            return
        
        # Create default location
        self.stdout.write(self.style.WARNING('Creating default inventory location...'))
        
        default_location = InventoryLocation.objects.create(
            id_location='LOC-0001',
            name='Bodega Principal',
            code='MAIN',
            main_location=True,
            location='Ubicación principal del almacén',
            status=True
        )
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(
            self.style.SUCCESS(
                f'✓ Created default location: {default_location.code} - {default_location.name}'
            )
        )
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                'Default inventory location created successfully!'
            )
        )
