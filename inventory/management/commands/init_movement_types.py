"""
Management command to initialize required MovementType records in the database.

Usage:
    python manage.py init_movement_types

This command creates the following movement types if they don't exist:
    - PURCHASE_IN (Entrada por Compra): Material received from purchase orders
    - SALE_OUT (Salida por Venta): Material sent for sales
    - ADJUSTMENT_IN (Ajuste Entrada): Manual increase adjustment
    - ADJUSTMENT_OUT (Ajuste Salida): Manual decrease adjustment
    - TRANSFER_IN (Transferencia Entrada): Material received from transfer
    - TRANSFER_OUT (Transferencia Salida): Material sent in transfer
"""

from django.core.management.base import BaseCommand
from inventory.models import MovementType


class Command(BaseCommand):
    help = 'Initialize required MovementType records in the database'

    def handle(self, *args, **options):
        """
        Create default MovementType records if they don't exist.
        """
        
        # Define the required movement types with their names and symbols
        required_types = [
            {'name': 'Entrada por Compra', 'symbol': 'PURCHASE_IN'},
            {'name': 'Salida por Venta', 'symbol': 'SALE_OUT'},
            {'name': 'Ajuste Entrada', 'symbol': 'ADJUSTMENT_IN'},
            {'name': 'Ajuste Salida', 'symbol': 'ADJUSTMENT_OUT'},
            {'name': 'Transferencia Entrada', 'symbol': 'TRANSFER_IN'},
            {'name': 'Transferencia Salida', 'symbol': 'TRANSFER_OUT'},
        ]
        
        created_count = 0
        existing_count = 0
        
        self.stdout.write(self.style.WARNING('Initializing MovementType records...'))
        self.stdout.write('')
        
        for type_data in required_types:
            # Check if type already exists by symbol (unique field)
            movement_type, created = MovementType.objects.get_or_create(
                symbol=type_data['symbol'],
                defaults={'name': type_data['name']}
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created: {movement_type.name} ({movement_type.symbol})'
                    )
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'• Already exists: {movement_type.name} ({movement_type.symbol})'
                    )
                )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  Created: {created_count} type(s)'))
        self.stdout.write(self.style.WARNING(f'  Already existed: {existing_count} type(s)'))
        self.stdout.write(self.style.SUCCESS(f'  Total: {created_count + existing_count} type(s)'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        if created_count > 0:
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(
                    'MovementType initialization completed successfully!'
                )
            )
        else:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    'All required MovementType records already exist.'
                )
            )
