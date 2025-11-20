"""
Comando para crear cuentas contables esenciales del sistema ERP.
"""

from django.core.management.base import BaseCommand
from accounting.models import AccountAccount, AccountType, AccountNature, AccountGroup
from core.models import Currency, Country, Status
import uuid


class Command(BaseCommand):
    help = 'Crea las cuentas contables esenciales necesarias para el funcionamiento del ERP'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Creando cuentas contables esenciales...'))
        
        # Obtener tipos y naturalezas
        try:
            asset_type = AccountType.objects.get(name='Asset')
            liability_type = AccountType.objects.get(name='Libiality')  # Nota: typo en DB
            debit_nature = AccountNature.objects.get(symbol='DR')
            credit_nature = AccountNature.objects.get(symbol='CR')
        except (AccountType.DoesNotExist, AccountNature.DoesNotExist) as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
            self.stdout.write(self.style.WARNING('Asegúrese de que existan tipos de cuenta y naturalezas básicos'))
            return
        
        # Buscar o crear tipo de cuenta para Ingresos
        try:
            revenue_type = AccountType.objects.get(name='Revenue')
        except AccountType.DoesNotExist:
            revenue_type = AccountType.objects.create(
                id_account_type='4',
                name='Revenue',
                description='Cuentas de Ingresos'
            )
        
        # Buscar o crear tipo de cuenta para Gastos
        try:
            expense_type = AccountType.objects.get(name='Expense')
        except AccountType.DoesNotExist:
            expense_type = AccountType.objects.create(
                id_account_type='5',
                name='Expense',
                description='Cuentas de Gastos'
            )
        
        # Obtener valores por defecto para campos requeridos
        try:
            default_group = AccountGroup.objects.first()
            if not default_group:
                self.stdout.write(self.style.ERROR('No hay AccountGroup configurado'))
                return
            
            default_currency = Currency.objects.first()
            if not default_currency:
                self.stdout.write(self.style.ERROR('No hay Currency configurada'))
                return
            
            default_country = Country.objects.first()
            if not default_country:
                self.stdout.write(self.style.ERROR('No hay Country configurado'))
                return
            
            default_status = Status.objects.first()
            if not default_status:
                self.stdout.write(self.style.ERROR('No hay Status configurado'))
                return
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error obteniendo valores por defecto: {e}'))
            return
        
        # Lista de cuentas esenciales
        accounts_to_create = [
            {
                'code': '1.1.03',
                'name': 'Cuentas por Cobrar',
                'description': 'Cuentas por cobrar a clientes',
                'account_type': asset_type,
                'nature': debit_nature,
            },
            {
                'code': '1.1.05',
                'name': 'Inventario',
                'description': 'Inventario de materiales y productos',
                'account_type': asset_type,
                'nature': debit_nature,
            },
            {
                'code': '2.1.01',
                'name': 'Cuentas por Pagar',
                'description': 'Cuentas por pagar a proveedores',
                'account_type': liability_type,
                'nature': credit_nature,
            },
            {
                'code': '4.1.01',
                'name': 'Ingresos por Ventas',
                'description': 'Ingresos por ventas de productos',
                'account_type': revenue_type,
                'nature': credit_nature,
            },
            {
                'code': '5.1.05',
                'name': 'Ajustes de Inventario',
                'description': 'Pérdidas y ganancias por ajustes de inventario',
                'account_type': expense_type,
                'nature': debit_nature,
            },
            {
                'code': '1.1.06',
                'name': 'Inventario Producto Terminado',
                'description': 'Inventario de productos terminados',
                'account_type': asset_type,
                'nature': debit_nature,
            },
        ]
        
        created_count = 0
        existing_count = 0
        
        for account_data in accounts_to_create:
            code = account_data['code']
            name = account_data['name']
            
            # Verificar si ya existe
            if AccountAccount.objects.filter(code=code).exists():
                self.stdout.write(self.style.WARNING(f'  ⚠ Cuenta {code} ({name}) ya existe'))
                existing_count += 1
                continue
            
            # Agregar campos por defecto
            account_data['id_account'] = str(uuid.uuid4())
            account_data['account_group'] = default_group
            account_data['currency'] = default_currency
            account_data['country'] = default_country
            account_data['status'] = default_status
            
            # Crear la cuenta
            try:
                account = AccountAccount.objects.create(**account_data)
                self.stdout.write(self.style.SUCCESS(f'  ✓ Cuenta {code} ({name}) creada exitosamente'))
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error al crear cuenta {code}: {str(e)}'))
        
        # Resumen
        self.stdout.write('')
        self.stdout.write(self.style.MIGRATE_HEADING('RESUMEN:'))
        self.stdout.write(self.style.SUCCESS(f'  Cuentas creadas: {created_count}'))
        self.stdout.write(self.style.WARNING(f'  Cuentas existentes: {existing_count}'))
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✓ Proceso completado'))
