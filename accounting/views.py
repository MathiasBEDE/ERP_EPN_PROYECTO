from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from .models import JournalEntry, JournalEntryLine
from datetime import datetime, date


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
