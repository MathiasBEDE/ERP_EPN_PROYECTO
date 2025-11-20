"""
Utilidades para generacion automatica de asientos contables.
Integracion con modulos de Compras, Ventas, Produccion e Inventario.
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from .models import JournalEntry, JournalEntryLine, AccountAccount
from core.models import Currency
import logging

logger = logging.getLogger(__name__)


# ==================== TAREA 2: ASIENTOS PARA COMPRAS ====================

def create_entry_for_purchase(purchase_order, user=None):
    """
    Crea un asiento contable para una orden de compra RECIBIDA.
    
    Asiento:
        Debito:  Inventario (Activo)
        Credito: Cuentas por Pagar (Pasivo)
    
    Args:
        purchase_order: Instancia de PurchaseOrder
        user: Usuario que crea el asiento (opcional)
    
    Returns:
        JournalEntry creado o None si ya existe
    """
    try:
        # Verificar si ya existe un asiento para esta orden
        existing = JournalEntry.objects.filter(
            reference=purchase_order.id_purchase_order,
            operation_type='PURCHASE'
        ).exists()
        
        if existing:
            logger.info(f"Ya existe asiento contable para compra {purchase_order.id_purchase_order}")
            return None
        
        with transaction.atomic():
            # Obtener moneda de la primera línea del pedido
            first_line = purchase_order.lines.first()
            currency = first_line.currency_supplier if first_line else Currency.objects.first()
            if not currency:
                raise ValidationError('No hay moneda configurada en el sistema')
            
            # Generar ID del asiento
            journal_entry_id = JournalEntry.generate_journal_entry_id()
            
            # Calcular total de la compra
            total = Decimal('0.00')
            for line in purchase_order.lines.all():
                line_total = Decimal(str(line.quantity)) * line.price
                total += line_total
            
            if total == 0:
                logger.warning(f"Compra {purchase_order.id_purchase_order} tiene total 0, no se crea asiento")
                return None
            
            # Crear asiento contable
            journal_entry = JournalEntry.objects.create(
                id_journal_entry=journal_entry_id,
                date=purchase_order.estimated_delivery_date or date.today(),
                description=f"Recepcion de compra {purchase_order.id_purchase_order} - Proveedor: {purchase_order.supplier.name}",
                operation_type='PURCHASE',
                reference=purchase_order.id_purchase_order,
                module='PURCHASES',
                currency=currency,
                status='DRAFT',
                created_by=user
            )
            
            # Buscar cuentas contables
            try:
                # Cuenta de Inventario (Activo - Debito)
                inventory_account = AccountAccount.objects.get(code='1.1.05')
            except AccountAccount.DoesNotExist:
                # Buscar primera cuenta de tipo Activo
                inventory_account = AccountAccount.objects.filter(
                    account_type__name__icontains='Activo'
                ).first()
                if not inventory_account:
                    raise ValidationError(
                        'No se encontro cuenta de Inventario. '
                        'Por favor, crea una cuenta con codigo 1.1.05 (Inventario)'
                    )
            
            try:
                # Cuenta de Cuentas por Pagar (Pasivo - Credito)
                payable_account = AccountAccount.objects.get(code='2.1.01')
            except AccountAccount.DoesNotExist:
                # Buscar primera cuenta de tipo Pasivo
                payable_account = AccountAccount.objects.filter(
                    account_type__name__icontains='Pasivo'
                ).first()
                if not payable_account:
                    raise ValidationError(
                        'No se encontro cuenta de Cuentas por Pagar. '
                        'Por favor, crea una cuenta con codigo 2.1.01 (Cuentas por Pagar)'
                    )
            
            # Crear linea de debito (Inventario)
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=inventory_account,
                description=f"Compra de materiales - {purchase_order.supplier.name}",
                debit=total,
                credit=Decimal('0.00'),
                position=1
            )
            
            # Crear linea de credito (Cuentas por Pagar)
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=payable_account,
                description=f"Adeudo a proveedor {purchase_order.supplier.name}",
                debit=Decimal('0.00'),
                credit=total,
                position=2
            )
            
            logger.info(f"Asiento contable {journal_entry_id} creado para compra {purchase_order.id_purchase_order} por {total}")
            return journal_entry
            
    except Exception as e:
        logger.error(f"Error al crear asiento contable para compra {purchase_order.id_purchase_order}: {str(e)}")
        raise


# ==================== TAREA 3: ASIENTOS PARA VENTAS ====================

def create_entry_for_sale(sales_order, user=None):
    """
    Crea asientos contables para una orden de venta ENTREGADA.
    
    Asiento 1 - Venta:
        Debito:  Cuentas por Cobrar (Activo)
        Credito: Ingresos por Ventas (Ingreso)
    
    Args:
        sales_order: Instancia de SalesOrder
        user: Usuario que crea el asiento (opcional)
    
    Returns:
        JournalEntry creado o None si ya existe
    """
    print(f"\n=== DEBUG: Entrando a create_entry_for_sale para orden {sales_order.id_sales_order} ===")
    try:
        # Verificar si ya existe un asiento para esta orden
        existing = JournalEntry.objects.filter(
            reference=sales_order.id_sales_order,
            operation_type='SALE'
        ).exists()
        
        if existing:
            logger.info(f"Ya existe asiento contable para venta {sales_order.id_sales_order}")
            print(f"DEBUG: Ya existe asiento para {sales_order.id_sales_order}")
            return None
        
        with transaction.atomic():
            # Obtener moneda (usar la primera moneda de las lineas)
            first_line = sales_order.lines.first()
            currency = first_line.currency_customer if first_line else Currency.objects.first()
            
            if not currency:
                raise ValidationError('No hay moneda configurada en el sistema')
            
            # Generar ID del asiento
            journal_entry_id = JournalEntry.generate_journal_entry_id()
            
            # Calcular total de la venta
            total = Decimal('0.00')
            for line in sales_order.lines.all():
                line_total = Decimal(str(line.quantity)) * line.price
                total += line_total
            
            print(f"DEBUG: Total calculado para venta: {total}")
            
            if total == 0:
                logger.warning(f"Venta {sales_order.id_sales_order} tiene total 0, no se crea asiento")
                print(f"DEBUG: Total es 0, no se crea asiento")
                return None
            
            # Crear asiento contable
            journal_entry = JournalEntry.objects.create(
                id_journal_entry=journal_entry_id,
                date=sales_order.issue_date or date.today(),
                description=f"Venta entregada {sales_order.id_sales_order} - Cliente: {sales_order.customer.name}",
                operation_type='SALE',
                reference=sales_order.id_sales_order,
                module='SALES',
                currency=currency,
                status='DRAFT',
                created_by=user
            )
            
            # Buscar cuentas contables
            print(f"DEBUG: Buscando cuenta de Cuentas por Cobrar (1.1.03)...")
            try:
                # Cuenta de Cuentas por Cobrar (Activo - Debito)
                receivable_account = AccountAccount.objects.get(code='1.1.03')
                print(f"DEBUG: Cuenta por Cobrar encontrada: {receivable_account.code} - {receivable_account.name}")
            except AccountAccount.DoesNotExist:
                print(f"DEBUG: Cuenta 1.1.03 no existe, buscando alternativa...")
                receivable_account = AccountAccount.objects.filter(
                    account_type__name__icontains='Activo'
                ).first()
                if not receivable_account:
                    error_msg = (
                        'No se encontro cuenta de Cuentas por Cobrar. '
                        'Por favor, crea una cuenta con codigo 1.1.03 (Cuentas por Cobrar)'
                    )
                    print(f"DEBUG ERROR: {error_msg}")
                    raise ValidationError(error_msg)
            
            print(f"DEBUG: Buscando cuenta de Ingresos (4.1.01)...")
            try:
                # Cuenta de Ingresos por Ventas (Ingreso - Credito)
                revenue_account = AccountAccount.objects.get(code='4.1.01')
                print(f"DEBUG: Cuenta de Ingresos encontrada: {revenue_account.code} - {revenue_account.name}")
            except AccountAccount.DoesNotExist:
                print(f"DEBUG: Cuenta 4.1.01 no existe, buscando alternativa...")
                revenue_account = AccountAccount.objects.filter(
                    account_type__name__icontains='Ingreso'
                ).first()
                if not revenue_account:
                    error_msg = (
                        'No se encontro cuenta de Ingresos. '
                        'Por favor, crea una cuenta con codigo 4.1.01 (Ingresos por Ventas)'
                    )
                    print(f"DEBUG ERROR: {error_msg}")
                    raise ValidationError(error_msg)
            
            # Crear linea de debito (Cuentas por Cobrar)
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=receivable_account,
                description=f"Venta a cliente {sales_order.customer.name}",
                debit=total,
                credit=Decimal('0.00'),
                position=1
            )
            
            # Crear linea de credito (Ingresos por Ventas)
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=revenue_account,
                description=f"Ingreso por venta - {sales_order.customer.name}",
                debit=Decimal('0.00'),
                credit=total,
                position=2
            )
            
            # TODO: Agregar asiento de costo de ventas cuando se implemente costeo de inventario
            
            print(f"DEBUG: ✓ Asiento contable {journal_entry_id} creado exitosamente para venta {sales_order.id_sales_order} por {total}")
            logger.info(f"Asiento contable {journal_entry_id} creado para venta {sales_order.id_sales_order} por {total}")
            return journal_entry
            
    except Exception as e:
        print(f"DEBUG ERROR: Excepción en create_entry_for_sale: {type(e).__name__}: {str(e)}")
        logger.error(f"Error al crear asiento contable para venta {sales_order.id_sales_order}: {str(e)}")
        raise


# ==================== TAREA 4: ASIENTOS PARA PRODUCCION ====================

def create_entry_for_production(work_order, user=None):
    """
    Crea un asiento contable para una orden de produccion TERMINADA.
    
    Asiento:
        Debito:  Inventario Producto Terminado (Activo)
        Credito: Inventario Materia Prima / Produccion en Proceso (Activo)
    
    Args:
        work_order: Instancia de WorkOrder
        user: Usuario que crea el asiento (opcional)
    
    Returns:
        JournalEntry creado o None si ya existe
    """
    try:
        # Verificar si ya existe un asiento para esta orden
        existing = JournalEntry.objects.filter(
            reference=work_order.id_work_order,
            operation_type='PRODUCTION'
        ).exists()
        
        if existing:
            logger.info(f"Ya existe asiento contable para produccion {work_order.id_work_order}")
            return None
        
        with transaction.atomic():
            # Obtener moneda por defecto
            currency = Currency.objects.first()
            if not currency:
                raise ValidationError('No hay moneda configurada en el sistema')
            
            # Generar ID del asiento
            journal_entry_id = JournalEntry.generate_journal_entry_id()
            
            # Calcular valor de produccion
            # TODO: Implementar calculo de costos real basado en materiales consumidos
            # Por ahora usamos un valor estimado basado en cantidad producida
            total = Decimal(str(work_order.quantity_to_produce)) * Decimal('100.00')
            
            if total == 0:
                logger.warning(f"Produccion {work_order.id_work_order} tiene cantidad 0, no se crea asiento")
                return None
            
            # Crear asiento contable
            journal_entry = JournalEntry.objects.create(
                id_journal_entry=journal_entry_id,
                date=work_order.scheduled_start_date or date.today(),
                description=f"Produccion terminada {work_order.id_work_order} - Material: {work_order.material.name}",
                operation_type='PRODUCTION',
                reference=work_order.id_work_order,
                module='MANUFACTURING',
                currency=currency,
                status='DRAFT',
                created_by=user
            )
            
            # Buscar cuentas contables
            try:
                # Cuenta de Inventario Producto Terminado (Activo - Debito)
                finished_goods_account = AccountAccount.objects.get(code='1.1.06')
            except AccountAccount.DoesNotExist:
                # Intentar con cuenta general de inventario
                try:
                    finished_goods_account = AccountAccount.objects.get(code='1.1.05')
                except AccountAccount.DoesNotExist:
                    finished_goods_account = AccountAccount.objects.filter(
                        account_type__name__icontains='Activo'
                    ).first()
                    if not finished_goods_account:
                        raise ValidationError(
                            'No se encontro cuenta de Inventario. '
                            'Por favor, crea una cuenta con codigo 1.1.06 (Producto Terminado) o 1.1.05 (Inventario)'
                        )
            
            try:
                # Cuenta de Inventario Materia Prima (Activo - Credito)
                raw_materials_account = AccountAccount.objects.get(code='1.1.05')
            except AccountAccount.DoesNotExist:
                raw_materials_account = AccountAccount.objects.filter(
                    account_type__name__icontains='Activo'
                ).first()
                if not raw_materials_account:
                    raise ValidationError(
                        'No se encontro cuenta de Inventario Materia Prima. '
                        'Por favor, crea una cuenta con codigo 1.1.05 (Inventario)'
                    )
            
            # Crear linea de debito (Producto Terminado)
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=finished_goods_account,
                description=f"Produccion de {work_order.quantity_to_produce} unidades de {work_order.material.name}",
                debit=total,
                credit=Decimal('0.00'),
                position=1
            )
            
            # Crear linea de credito (Materia Prima consumida)
            JournalEntryLine.objects.create(
                journal_entry=journal_entry,
                account=raw_materials_account,
                description=f"Consumo de materiales para produccion",
                debit=Decimal('0.00'),
                credit=total,
                position=2
            )
            
            logger.info(f"Asiento contable {journal_entry_id} creado para produccion {work_order.id_work_order} por {total}")
            return journal_entry
            
    except Exception as e:
        logger.error(f"Error al crear asiento contable para produccion {work_order.id_work_order}: {str(e)}")
        raise


# ==================== TAREA 5: ASIENTOS PARA AJUSTES DE INVENTARIO ====================

def create_entry_for_inventory_adjustment(movement, user=None):
    """
    Crea un asiento contable para un ajuste de inventario.
    
    Asiento (ajuste positivo - ADJUSTMENT_IN):
        Debito:  Inventario (Activo)
        Credito: Ganancia por Ajuste (Otro Ingreso)
    
    Asiento (ajuste negativo - ADJUSTMENT_OUT):
        Debito:  Perdida por Ajuste (Gasto)
        Credito: Inventario (Activo)
    
    Args:
        movement: Instancia de InventoryMovement
        user: Usuario que crea el asiento (opcional)
    
    Returns:
        JournalEntry creado o None si ya existe
    """
    try:
        # Verificar si ya existe un asiento para este movimiento
        existing = JournalEntry.objects.filter(
            reference=movement.id_inventory_movement,
            operation_type='ADJUSTMENT'
        ).exists()
        
        if existing:
            logger.info(f"Ya existe asiento contable para ajuste {movement.id_inventory_movement}")
            return None
        
        with transaction.atomic():
            # Obtener moneda por defecto
            currency = Currency.objects.first()
            if not currency:
                raise ValidationError('No hay moneda configurada en el sistema')
            
            # Generar ID del asiento
            journal_entry_id = JournalEntry.generate_journal_entry_id()
            
            # Calcular valor del ajuste
            # TODO: Usar costo unitario real cuando este implementado el costeo
            # Por ahora usamos un valor estimado
            total = abs(Decimal(str(movement.quantity))) * Decimal('50.00')
            
            if total == 0:
                logger.warning(f"Ajuste {movement.id_inventory_movement} tiene cantidad 0, no se crea asiento")
                return None
            
            # Determinar si es ajuste positivo o negativo
            movement_type_symbol = movement.movement_type.symbol
            is_positive = 'ADJUSTMENT_IN' in movement_type_symbol or movement_type_symbol.endswith('_IN')
            
            # Crear asiento contable
            journal_entry = JournalEntry.objects.create(
                id_journal_entry=journal_entry_id,
                date=movement.date or date.today(),
                description=f"Ajuste de inventario {movement.id_inventory_movement} - {movement.material.name} ({'Entrada' if is_positive else 'Salida'})",
                operation_type='ADJUSTMENT',
                reference=movement.id_inventory_movement,
                module='INVENTORY',
                currency=currency,
                status='DRAFT',
                created_by=user
            )
            
            # Buscar cuentas contables
            try:
                # Cuenta de Inventario (Activo)
                inventory_account = AccountAccount.objects.get(code='1.1.05')
            except AccountAccount.DoesNotExist:
                inventory_account = AccountAccount.objects.filter(
                    account_type__name__icontains='Activo'
                ).first()
                if not inventory_account:
                    raise ValidationError(
                        'No se encontro cuenta de Inventario. '
                        'Por favor, crea una cuenta con codigo 1.1.05 (Inventario)'
                    )
            
            try:
                # Cuenta de Ajustes (puede ser Ingreso o Gasto dependiendo del tipo)
                adjustment_account = AccountAccount.objects.get(code='5.1.05')
            except AccountAccount.DoesNotExist:
                # Buscar cuenta de gastos o ingresos
                adjustment_account = AccountAccount.objects.filter(
                    account_type__name__icontains='Gasto'
                ).first() or AccountAccount.objects.filter(
                    account_type__name__icontains='Ingreso'
                ).first()
                if not adjustment_account:
                    raise ValidationError(
                        'No se encontro cuenta de Ajustes. '
                        'Por favor, crea una cuenta con codigo 5.1.05 (Ajustes de Inventario)'
                    )
            
            if is_positive:
                # Ajuste positivo: Debito Inventario, Credito Ganancia
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    account=inventory_account,
                    description=f"Ajuste positivo - {movement.material.name} ({movement.quantity} unidades)",
                    debit=total,
                    credit=Decimal('0.00'),
                    position=1
                )
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    account=adjustment_account,
                    description=f"Ganancia por ajuste de inventario",
                    debit=Decimal('0.00'),
                    credit=total,
                    position=2
                )
            else:
                # Ajuste negativo: Debito Perdida, Credito Inventario
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    account=adjustment_account,
                    description=f"Perdida por ajuste - {movement.material.name} ({abs(movement.quantity)} unidades)",
                    debit=total,
                    credit=Decimal('0.00'),
                    position=1
                )
                JournalEntryLine.objects.create(
                    journal_entry=journal_entry,
                    account=inventory_account,
                    description=f"Reduccion de inventario",
                    debit=Decimal('0.00'),
                    credit=total,
                    position=2
                )
            
            logger.info(f"Asiento contable {journal_entry_id} creado para ajuste {movement.id_inventory_movement} por {total}")
            return journal_entry
            
    except Exception as e:
        logger.error(f"Error al crear asiento contable para ajuste {movement.id_inventory_movement}: {str(e)}")
        raise


# ==================== FUNCIONES AUXILIARES ====================

def post_journal_entry(journal_entry_id):
    """
    Contabiliza un asiento (cambia estado a POSTED).
    
    Args:
        journal_entry_id: ID del asiento a contabilizar
    
    Returns:
        JournalEntry actualizado
    """
    try:
        journal_entry = JournalEntry.objects.get(id_journal_entry=journal_entry_id)
        journal_entry.post()
        logger.info(f"Asiento contable {journal_entry_id} contabilizado exitosamente")
        return journal_entry
    except JournalEntry.DoesNotExist:
        raise ValidationError(f"Asiento {journal_entry_id} no encontrado")
    except Exception as e:
        logger.error(f"Error al contabilizar asiento {journal_entry_id}: {str(e)}")
        raise


def cancel_journal_entry(journal_entry_id):
    """
    Anula un asiento (cambia estado a CANCELLED).
    
    Args:
        journal_entry_id: ID del asiento a anular
    
    Returns:
        JournalEntry actualizado
    """
    try:
        journal_entry = JournalEntry.objects.get(id_journal_entry=journal_entry_id)
        journal_entry.cancel()
        logger.info(f"Asiento contable {journal_entry_id} anulado exitosamente")
        return journal_entry
    except JournalEntry.DoesNotExist:
        raise ValidationError(f"Asiento {journal_entry_id} no encontrado")
    except Exception as e:
        logger.error(f"Error al anular asiento {journal_entry_id}: {str(e)}")
        raise


# ==================== TAREA 8: ACTUALIZACION DE SALDOS DE CUENTAS ====================

def update_account_balances_from_entry(journal_entry):
    """
    Actualiza los saldos (current_balance) de las cuentas afectadas por un asiento contable.
    
    Esta funcion debe llamarse despues de crear o contabilizar un asiento.
    Recorre todas las lineas del asiento y actualiza el saldo de cada cuenta segun su naturaleza:
    
    - Cuentas de naturaleza DEBIT (Activos, Gastos):
      * Debitos AUMENTAN el saldo (+)
      * Creditos DISMINUYEN el saldo (-)
    
    - Cuentas de naturaleza CREDIT (Pasivos, Patrimonio, Ingresos):
      * Creditos AUMENTAN el saldo (+)
      * Debitos DISMINUYEN el saldo (-)
    
    Estos saldos actualizados sirven para:
    - Balance General: Sumar activos, pasivos y patrimonio por grupos
    - Estado de Resultados: Sumar ingresos y gastos
    - Reportes financieros en tiempo real
    - Auditoria y conciliaciones
    
    Args:
        journal_entry: Instancia de JournalEntry (debe estar en estado POSTED)
    
    Returns:
        dict: Diccionario con las cuentas actualizadas y sus nuevos saldos
    """
    
    if not journal_entry:
        logger.warning("No se proporciono asiento contable para actualizar saldos")
        return {}
    
    # Solo actualizar saldos si el asiento esta contabilizado
    if journal_entry.status != 'POSTED':
        logger.warning(
            f"Asiento {journal_entry.id_journal_entry} no esta contabilizado (estado: {journal_entry.status}). "
            "Los saldos solo se actualizan para asientos en estado POSTED."
        )
        return {}
    
    updated_accounts = {}
    
    try:
        with transaction.atomic():
            # Recorrer todas las lineas del asiento
            for line in journal_entry.lines.select_related('account', 'account__nature'):
                account = line.account
                nature_symbol = account.nature.symbol
                
                balance_change = Decimal('0.00')
                
                if nature_symbol == 'DEBIT':
                    # Cuentas de naturaleza DEBIT (Activos, Gastos):
                    # - Los debitos AUMENTAN el saldo
                    # - Los creditos DISMINUYEN el saldo
                    balance_change = line.debit - line.credit
                    
                elif nature_symbol == 'CREDIT':
                    # Cuentas de naturaleza CREDIT (Pasivos, Patrimonio, Ingresos):
                    # - Los creditos AUMENTAN el saldo
                    # - Los debitos DISMINUYEN el saldo
                    balance_change = line.credit - line.debit
                
                else:
                    logger.warning(
                        f"Naturaleza de cuenta desconocida '{nature_symbol}' "
                        f"para cuenta {account.code} - {account.name}"
                    )
                    continue
                
                # Actualizar el saldo de la cuenta
                account.current_balance += balance_change
                account.save(update_fields=['current_balance', 'updated_at'])
                
                updated_accounts[f"{account.code} - {account.name}"] = account.current_balance
                
                logger.debug(
                    f"Cuenta {account.code} actualizada: "
                    f"Cambio={balance_change}, Nuevo saldo={account.current_balance}"
                )
            
            logger.info(
                f"Saldos actualizados para {len(updated_accounts)} cuenta(s) "
                f"del asiento {journal_entry.id_journal_entry}"
            )
            
    except Exception as e:
        logger.error(
            f"Error al actualizar saldos para asiento {journal_entry.id_journal_entry}: {str(e)}"
        )
        raise ValidationError(f"Error al actualizar saldos de cuentas: {str(e)}")
    
    return updated_accounts


def recalculate_all_account_balances():
    """
    Recalcula todos los saldos de cuentas desde cero basandose en asientos contabilizados.
    
    Util para:
    - Inicializacion del sistema
    - Correccion de inconsistencias
    - Migracion de datos
    - Auditoria y reconciliacion
    
    ADVERTENCIA: Esta operacion puede ser costosa en sistemas con muchos asientos.
    
    Returns:
        dict: Resumen de cuentas actualizadas
    """
    try:
        with transaction.atomic():
            # Resetear todos los saldos a cero
            AccountAccount.objects.all().update(current_balance=Decimal('0.00'))
            
            # Obtener todos los asientos contabilizados, ordenados por fecha
            posted_entries = JournalEntry.objects.filter(
                status='POSTED'
            ).order_by('date', 'created_at')
            
            total_entries = posted_entries.count()
            logger.info(f"Recalculando saldos basandose en {total_entries} asientos contabilizados...")
            
            # Procesar cada asiento
            for idx, entry in enumerate(posted_entries, 1):
                update_account_balances_from_entry(entry)
                
                if idx % 100 == 0:
                    logger.info(f"Procesados {idx}/{total_entries} asientos...")
            
            # Obtener resumen de cuentas con saldo
            accounts_with_balance = AccountAccount.objects.exclude(
                current_balance=Decimal('0.00')
            ).count()
            
            summary = {
                'total_entries_processed': total_entries,
                'accounts_with_balance': accounts_with_balance,
                'status': 'success'
            }
            
            logger.info(
                f"Recalculacion completada: {total_entries} asientos procesados, "
                f"{accounts_with_balance} cuentas con saldo"
            )
            
            return summary
            
    except Exception as e:
        logger.error(f"Error al recalcular saldos de cuentas: {str(e)}")
        raise ValidationError(f"Error en recalculacion de saldos: {str(e)}")
