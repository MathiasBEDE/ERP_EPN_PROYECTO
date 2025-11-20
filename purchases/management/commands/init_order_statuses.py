"""
Management command to initialize required OrderStatus records in the database.

Usage:
    python manage.py init_order_statuses

This command creates the following order statuses if they don't exist:
    - DRAFT (Borrador): Initial state when creating a new order
    - CONFIRMED (Confirmado): Order has been confirmed
    - RECEIVED (Recibido): Purchase order has been received
    - DELIVERED (Entregada): Sales order has been delivered
    - CANCELLED (Cancelado): Order was cancelled
    - CLOSED (Cerrado): Order is closed
    - INVOICED (Facturado): Order has been invoiced
"""

from django.core.management.base import BaseCommand
from purchases.models import OrderStatus


class Command(BaseCommand):
    help = 'Initialize required OrderStatus records in the database'

    def handle(self, *args, **options):
        """
        Create default OrderStatus records if they don't exist.
        """
        
        # Define the required statuses with their names and symbols
        required_statuses = [
            {'name': 'Borrador', 'symbol': 'DRAFT'},
            {'name': 'Confirmado', 'symbol': 'CONFIRMED'},
            {'name': 'Recibido', 'symbol': 'RECEIVED'},
            {'name': 'Cancelado', 'symbol': 'CANCELLED'},
            {'name': 'Cerrado', 'symbol': 'CLOSED'},
            {'name': 'Facturado', 'symbol': 'INVOICED'},
            {'name': 'Entregada', 'symbol': 'DELIVERED'},
        ]
        
        created_count = 0
        existing_count = 0
        
        self.stdout.write(self.style.WARNING('Initializing OrderStatus records...'))
        self.stdout.write('')
        
        for status_data in required_statuses:
            # Check if status already exists by symbol (unique field)
            status, created = OrderStatus.objects.get_or_create(
                symbol=status_data['symbol'],
                defaults={'name': status_data['name']}
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Created: {status.name} ({status.symbol})'
                    )
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'• Already exists: {status.name} ({status.symbol})'
                    )
                )
        
        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Summary:'))
        self.stdout.write(self.style.SUCCESS(f'  Created: {created_count} status(es)'))
        self.stdout.write(self.style.WARNING(f'  Already existed: {existing_count} status(es)'))
        self.stdout.write(self.style.SUCCESS(f'  Total: {created_count + existing_count} status(es)'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        if created_count > 0:
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS(
                    'OrderStatus initialization completed successfully!'
                )
            )
        else:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    'All required OrderStatus records already exist.'
                )
            )
