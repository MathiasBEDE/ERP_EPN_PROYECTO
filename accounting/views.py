from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import JournalEntry, JournalEntryLine
from .utils import update_account_balances_from_entry
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


def journal_entry_list_view(request):
    """
    Vista para listar asientos contables con filtros y paginación.
    
    Filtros disponibles:
    - Rango de fechas (desde/hasta)
    - Tipo de operación
    - Módulo
    - Referencia (búsqueda parcial)
    - Estado
    """
    # Obtener todos los asientos ordenados por fecha descendente
    entries = JournalEntry.objects.select_related(
        'currency',
        'created_by'
    ).prefetch_related(
        'lines__account'
    ).order_by('-date', '-id_journal_entry')
    
    # FILTROS
    # Filtro por rango de fechas
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if fecha_desde:
        try:
            fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
            entries = entries.filter(date__gte=fecha_desde_obj)
        except ValueError:
            messages.warning(request, 'Formato de fecha inválido para "Fecha Desde"')
    
    if fecha_hasta:
        try:
            fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
            entries = entries.filter(date__lte=fecha_hasta_obj)
        except ValueError:
            messages.warning(request, 'Formato de fecha inválido para "Fecha Hasta"')
    
    # Filtro por tipo de operación
    operation_type = request.GET.get('operation_type')
    if operation_type and operation_type != '':
        entries = entries.filter(operation_type=operation_type)
    
    # Filtro por módulo
    module = request.GET.get('module')
    if module and module != '':
        entries = entries.filter(module=module)
    
    # Filtro por referencia (búsqueda parcial)
    reference = request.GET.get('reference')
    if reference and reference.strip():
        entries = entries.filter(reference__icontains=reference.strip())
    
    # Filtro por estado
    status = request.GET.get('status')
    if status and status != '':
        entries = entries.filter(status=status)
    
    # Paginación
    paginator = Paginator(entries, 25)  # 25 asientos por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calcular totales para cada asiento en la página
    entries_with_totals = []
    for entry in page_obj:
        total_debit = entry.get_total_debit()
        total_credit = entry.get_total_credit()
        is_balanced = entry.is_balanced()
        
        entries_with_totals.append({
            'entry': entry,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'is_balanced': is_balanced,
        })
    
    context = {
        'page_obj': page_obj,
        'entries_with_totals': entries_with_totals,
        'operation_types': JournalEntry.OPERATION_TYPE_CHOICES,
        'modules': JournalEntry.MODULE_CHOICES,
        'status_choices': JournalEntry.STATUS_CHOICES,
        # Mantener valores de filtros en el formulario
        'fecha_desde': fecha_desde or '',
        'fecha_hasta': fecha_hasta or '',
        'selected_operation_type': operation_type or '',
        'selected_module': module or '',
        'reference': reference or '',
        'selected_status': status or '',
    }
    
    return render(request, 'accounting/journal_entry_list.html', context)


def journal_entry_detail_view(request, id_journal_entry):
    """
    Vista para mostrar el detalle de un asiento contable con todas sus líneas.
    
    Muestra:
    - Información del encabezado del asiento
    - Tabla de líneas con cuenta, descripción, debe, haber
    - Totales de debe y haber
    - Estado de balance
    
    También maneja las acciones POST:
    - contabilizar: Cambia estado a POSTED y actualiza saldos
    - anular: Cambia estado a CANCELLED y revierte saldos
    """
    entry = get_object_or_404(
        JournalEntry.objects.select_related(
            'currency',
            'created_by'
        ).prefetch_related(
            'lines__account__nature',
            'lines__account__account_type'
        ),
        id_journal_entry=id_journal_entry
    )
    
    # Manejar acciones POST
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'post':
            # CONTABILIZAR ASIENTO
            try:
                with transaction.atomic():
                    # Verificar que esté en DRAFT
                    if entry.status != 'DRAFT':
                        messages.error(
                            request,
                            f'No se puede contabilizar un asiento en estado {entry.get_status_display()}'
                        )
                        return redirect('accounting:journal_entry_detail', id_journal_entry=entry.id_journal_entry)
                    
                    # Contabilizar (cambia a POSTED)
                    entry.post()
                    
                    # Actualizar saldos de cuentas
                    try:
                        updated_accounts = update_account_balances_from_entry(entry)
                        logger.info(f'Asiento {entry.id_journal_entry} contabilizado. Cuentas actualizadas: {len(updated_accounts)}')
                        
                        messages.success(
                            request,
                            f'✓ Asiento {entry.id_journal_entry} contabilizado exitosamente. '
                            f'Se actualizaron {len(updated_accounts)} cuenta(s).'
                        )
                    except Exception as e:
                        logger.error(f'Error al actualizar saldos: {str(e)}')
                        messages.warning(
                            request,
                            f'Asiento contabilizado pero hubo un error al actualizar saldos: {str(e)}'
                        )
                    
            except ValidationError as e:
                messages.error(request, f'Error: {str(e)}')
            except Exception as e:
                logger.error(f'Error al contabilizar asiento {entry.id_journal_entry}: {str(e)}')
                messages.error(request, f'Error al contabilizar: {str(e)}')
            
            return redirect('accounting:journal_entry_detail', id_journal_entry=entry.id_journal_entry)
        
        elif action == 'cancel':
            # ANULAR ASIENTO
            try:
                with transaction.atomic():
                    # Verificar que esté en POSTED
                    if entry.status != 'POSTED':
                        messages.error(
                            request,
                            f'No se puede anular un asiento en estado {entry.get_status_display()}'
                        )
                        return redirect('accounting:journal_entry_detail', id_journal_entry=entry.id_journal_entry)
                    
                    # Revertir saldos ANTES de anular
                    try:
                        for line in entry.lines.select_related('account', 'account__nature'):
                            account = line.account
                            nature_symbol = account.nature.symbol
                            
                            # Revertir el cambio (operación inversa)
                            if nature_symbol == 'DR':  # DEBIT
                                balance_change = -(line.debit - line.credit)
                            elif nature_symbol == 'CR':  # CREDIT
                                balance_change = -(line.credit - line.debit)
                            else:
                                continue
                            
                            account.current_balance += balance_change
                            account.save(update_fields=['current_balance', 'updated_at'])
                        
                        logger.info(f'Saldos revertidos para asiento {entry.id_journal_entry}')
                    except Exception as e:
                        logger.error(f'Error al revertir saldos: {str(e)}')
                        raise ValidationError(f'Error al revertir saldos: {str(e)}')
                    
                    # Anular (cambia a CANCELLED)
                    entry.cancel()
                    
                    messages.success(
                        request,
                        f'✓ Asiento {entry.id_journal_entry} anulado exitosamente. Los saldos fueron revertidos.'
                    )
                    
            except ValidationError as e:
                messages.error(request, f'Error: {str(e)}')
            except Exception as e:
                logger.error(f'Error al anular asiento {entry.id_journal_entry}: {str(e)}')
                messages.error(request, f'Error al anular: {str(e)}')
            
            return redirect('accounting:journal_entry_detail', id_journal_entry=entry.id_journal_entry)
    
    # GET - Mostrar detalle
    # Obtener líneas ordenadas por posición
    lines = entry.lines.all().order_by('position')
    
    # Calcular totales
    total_debit = entry.get_total_debit()
    total_credit = entry.get_total_credit()
    is_balanced = entry.is_balanced()
    
    # Determinar si se puede contabilizar o anular
    can_post = entry.status == 'DRAFT' and is_balanced
    can_cancel = entry.status == 'POSTED'
    
    context = {
        'entry': entry,
        'lines': lines,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'is_balanced': is_balanced,
        'can_post': can_post,
        'can_cancel': can_cancel,
    }
    
    return render(request, 'accounting/journal_entry_detail.html', context)
