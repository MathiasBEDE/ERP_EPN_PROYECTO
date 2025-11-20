"""
Script de prueba para el módulo de contabilidad.
Ejecutar con: python manage.py shell < accounting/test_accounting.py
"""

from decimal import Decimal
from datetime import date
from accounting.models import JournalEntry, JournalEntryLine, AccountAccount
from core.models import Currency

print("\n" + "="*80)
print("PRUEBA DEL MÓDULO DE CONTABILIDAD")
print("="*80 + "\n")

# Test 1: Generar ID secuencial
print("Test 1: Generación de ID secuencial")
print("-" * 40)
new_id = JournalEntry.generate_journal_entry_id()
print(f"✅ Nuevo ID generado: {new_id}\n")

# Test 2: Crear asiento contable de prueba
print("Test 2: Crear asiento contable")
print("-" * 40)

try:
    # Obtener moneda
    currency = Currency.objects.first()
    if not currency:
        print("❌ No hay monedas configuradas. Por favor, crea una moneda primero.")
    else:
        # Crear asiento
        journal_entry = JournalEntry.objects.create(
            id_journal_entry=JournalEntry.generate_journal_entry_id(),
            date=date.today(),
            description="Asiento de prueba del sistema",
            operation_type='MANUAL',
            reference='TEST-001',
            module='ACCOUNTING',
            currency=currency,
            status='DRAFT'
        )
        print(f"✅ Asiento creado: {journal_entry.id_journal_entry}")
        print(f"   Fecha: {journal_entry.date}")
        print(f"   Descripción: {journal_entry.description}")
        print(f"   Estado: {journal_entry.status}\n")
        
        # Test 3: Agregar líneas
        print("Test 3: Agregar líneas al asiento")
        print("-" * 40)
        
        # Buscar cuentas disponibles
        accounts = AccountAccount.objects.all()[:2]
        
        if len(accounts) < 2:
            print("❌ No hay suficientes cuentas configuradas.")
            print("   Por favor, crea al menos 2 cuentas en /admin/accounting/accountaccount/\n")
        else:
            # Línea de débito
            line1 = JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=accounts[0],
                description="Línea de débito de prueba",
                debit=Decimal('1000.00'),
                credit=Decimal('0.00'),
                position=1
            )
            print(f"✅ Línea 1 creada: {line1.account.code} - Débito: ${line1.debit}")
            
            # Línea de crédito
            line2 = JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=accounts[1],
                description="Línea de crédito de prueba",
                debit=Decimal('0.00'),
                credit=Decimal('1000.00'),
                position=2
            )
            print(f"✅ Línea 2 creada: {line2.account.code} - Crédito: ${line2.credit}\n")
            
            # Test 4: Verificar balance
            print("Test 4: Verificar balance del asiento")
            print("-" * 40)
            
            total_debit = journal_entry.get_total_debit()
            total_credit = journal_entry.get_total_credit()
            is_balanced = journal_entry.is_balanced()
            
            print(f"Total Débito:  ${total_debit}")
            print(f"Total Crédito: ${total_credit}")
            print(f"¿Balanceado?: {'✅ SÍ' if is_balanced else '❌ NO'}\n")
            
            # Test 5: Contabilizar asiento
            if is_balanced:
                print("Test 5: Contabilizar asiento")
                print("-" * 40)
                
                journal_entry.post()
                print(f"✅ Asiento contabilizado exitosamente")
                print(f"   Nuevo estado: {journal_entry.status}\n")
            
            # Test 6: Validación de línea incorrecta
            print("Test 6: Validación de línea incorrecta")
            print("-" * 40)
            
            try:
                # Intentar crear línea con débito y crédito simultáneos
                bad_line = JournalEntryLine(
                    journal_entry=journal_entry,
                    account=accounts[0],
                    debit=Decimal('100.00'),
                    credit=Decimal('100.00'),
                    position=3
                )
                bad_line.full_clean()  # Esto debe lanzar ValidationError
                print("❌ La validación falló - se permitió línea incorrecta")
            except Exception as e:
                print(f"✅ Validación correcta - Error esperado: {str(e)[:60]}...\n")
            
            print("="*80)
            print("PRUEBAS COMPLETADAS EXITOSAMENTE")
            print("="*80)
            print(f"\nPuedes ver el asiento creado en:")
            print(f"http://127.0.0.1:8000/admin/accounting/journalentry/{journal_entry.pk}/change/\n")
            
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nAsegúrate de tener:")
    print("1. Al menos una moneda configurada en Currency")
    print("2. Al menos dos cuentas configuradas en AccountAccount")
    print("3. Migraciones aplicadas correctamente\n")
