from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict

from sales.models import SalesOrder
from purchases.models import PurchaseOrder
from accounting.models import JournalEntry, AccountAccount
from inventory.models import InventoryMovement
from manufacturing.models import WorkOrder
from customers.models import Customer
from suppliers.models import Supplier


@login_required
def dashboard(request):
    """
    Vista principal del dashboard de reportería.
    Muestra métricas clave y tarjetas con información resumida.
    """
    # Calcular periodo actual (mes actual)
    today = timezone.now().date()
    first_day_month = today.replace(day=1)
    
    # Ventas del mes (conteo)
    sales_current_month = SalesOrder.objects.filter(
        status__symbol='DELIVERED',
        issue_date__gte=first_day_month
    ).count()
    
    # Compras del mes (conteo)
    purchases_current_month = PurchaseOrder.objects.filter(
        status__symbol__in=['RECEIVED', 'CLOSED'],
        created_at__gte=first_day_month
    ).count()
    
    # Órdenes de producción del mes
    production_current_month = WorkOrder.objects.filter(
        created_at__gte=first_day_month
    ).count()
    
    # Asientos contables del mes
    journal_entries_current_month = JournalEntry.objects.filter(
        date__gte=first_day_month
    ).count()
    
    # Calcular totales monetarios
    # Total de ventas completadas del mes
    monthly_sales_total = 0
    for sale in SalesOrder.objects.filter(status__symbol='DELIVERED', issue_date__gte=first_day_month):
        sale_total = sum(Decimal(str(line.quantity)) * line.price for line in sale.lines.all())
        monthly_sales_total += float(sale_total)
    
    # Total de compras recibidas del mes
    monthly_purchases_total = 0
    for purchase in PurchaseOrder.objects.filter(status__symbol__in=['RECEIVED', 'CLOSED'], created_at__gte=first_day_month):
        purchase_total = sum(Decimal(str(line.quantity)) * line.price for line in purchase.lines.all())
        monthly_purchases_total += float(purchase_total)
    
    # Beneficio neto
    net_benefit = monthly_sales_total - monthly_purchases_total
    
    context = {
        'sales_count': sales_current_month,
        'purchases_count': purchases_current_month,
        'production_count': production_current_month,
        'journal_entries_count': journal_entries_current_month,
        'monthly_sales_total': monthly_sales_total,
        'monthly_purchases_total': monthly_purchases_total,
        'net_benefit': net_benefit,
    }
    
    return render(request, 'reporting/dashboard.html', context)


@login_required
def sales_report(request):
    """Vista detallada de reporte de ventas con análisis por cliente y producto"""
    today = timezone.now().date()
    first_day_month = today.replace(day=1)
    
    # Filtros
    period = request.GET.get('period', 'month')
    customer_id = request.GET.get('customer')
    
    # Calcular fecha de inicio según periodo
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'quarter':
        start_date = first_day_month - timedelta(days=90)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    else:  # month
        start_date = first_day_month
    
    # Query base
    sales_query = SalesOrder.objects.filter(
        status__symbol='DELIVERED',
        issue_date__gte=start_date
    ).select_related('customer', 'status').prefetch_related('lines__material')
    
    if customer_id:
        sales_query = sales_query.filter(customer_id=customer_id)
    
    sales = sales_query.order_by('-issue_date')
    
    # Análisis por cliente
    from customers.models import Customer
    from django.db.models import Count
    
    customer_analysis = []
    for customer in Customer.objects.all():
        customer_sales = sales.filter(customer=customer)
        if customer_sales.exists():
            total = sum(
                sum(Decimal(str(line.quantity)) * line.price for line in sale.lines.all())
                for sale in customer_sales
            )
            customer_analysis.append({
                'customer': customer,
                'count': customer_sales.count(),
                'total': float(total)
            })
    
    customer_analysis.sort(key=lambda x: x['total'], reverse=True)
    
    # Top 5 productos más vendidos
    from collections import defaultdict
    product_sales = defaultdict(lambda: {'quantity': 0, 'total': 0, 'material': None})
    
    for sale in sales:
        for line in sale.lines.all():
            key = line.material.id
            product_sales[key]['material'] = line.material
            product_sales[key]['quantity'] += float(line.quantity)
            product_sales[key]['total'] += float(Decimal(str(line.quantity)) * line.price)
    
    top_products = sorted(product_sales.values(), key=lambda x: x['total'], reverse=True)[:5]
    
    # Totales generales
    total_sales = float(sum(
        sum(Decimal(str(line.quantity)) * line.price for line in sale.lines.all())
        for sale in sales
    ))
    
    # Comparativa con periodo anterior
    if period == 'month':
        prev_start = (first_day_month - timedelta(days=1)).replace(day=1)
        prev_end = first_day_month - timedelta(days=1)
    else:
        prev_start = start_date - (today - start_date)
        prev_end = start_date - timedelta(days=1)
    
    prev_sales = SalesOrder.objects.filter(
        status__symbol='DELIVERED',
        issue_date__gte=prev_start,
        issue_date__lte=prev_end
    )
    
    prev_total = float(sum(
        sum(Decimal(str(line.quantity)) * line.price for line in sale.lines.all())
        for sale in prev_sales
    ))
    
    if prev_total > 0:
        growth_percentage = ((total_sales - prev_total) / prev_total) * 100
    else:
        growth_percentage = 100 if total_sales > 0 else 0
    
    context = {
        'sales': sales,
        'period': period,
        'customer_analysis': customer_analysis[:10],  # Top 10
        'top_products': top_products,
        'total_sales': total_sales,
        'sales_count': sales.count(),
        'prev_total': prev_total,
        'growth_percentage': growth_percentage,
        'customers': Customer.objects.all(),
        'selected_customer': customer_id,
    }
    
    return render(request, 'reporting/sales_report.html', context)


@login_required
def purchases_report(request):
    """Vista detallada de reporte de compras con análisis por proveedor"""
    today = timezone.now().date()
    first_day_month = today.replace(day=1)
    
    # Filtros
    period = request.GET.get('period', 'month')
    supplier_id = request.GET.get('supplier')
    
    # Calcular fecha de inicio según periodo
    if period == 'week':
        start_date = today - timedelta(days=7)
    elif period == 'quarter':
        start_date = first_day_month - timedelta(days=90)
    elif period == 'year':
        start_date = today.replace(month=1, day=1)
    else:  # month
        start_date = first_day_month
    
    # Query base
    purchases_query = PurchaseOrder.objects.filter(
        status__symbol__in=['RECEIVED', 'CLOSED'],
        created_at__gte=start_date
    ).select_related('supplier', 'status').prefetch_related('lines__material')
    
    if supplier_id:
        purchases_query = purchases_query.filter(supplier_id=supplier_id)
    
    purchases = purchases_query.order_by('-created_at')
    
    # Análisis por proveedor
    from suppliers.models import Supplier
    
    supplier_analysis = []
    for supplier in Supplier.objects.all():
        supplier_purchases = purchases.filter(supplier=supplier)
        if supplier_purchases.exists():
            total = sum(
                sum(Decimal(str(line.quantity)) * line.price for line in purchase.lines.all())
                for purchase in supplier_purchases
            )
            supplier_analysis.append({
                'supplier': supplier,
                'count': supplier_purchases.count(),
                'total': float(total)
            })
    
    supplier_analysis.sort(key=lambda x: x['total'], reverse=True)
    
    # Top 5 materiales más comprados
    from collections import defaultdict
    material_purchases = defaultdict(lambda: {'quantity': 0, 'total': 0, 'material': None})
    
    for purchase in purchases:
        for line in purchase.lines.all():
            key = line.material.id
            material_purchases[key]['material'] = line.material
            material_purchases[key]['quantity'] += float(line.quantity)
            material_purchases[key]['total'] += float(Decimal(str(line.quantity)) * line.price)
    
    top_materials = sorted(material_purchases.values(), key=lambda x: x['total'], reverse=True)[:5]
    
    # Totales generales
    total_purchases = float(sum(
        sum(Decimal(str(line.quantity)) * line.price for line in purchase.lines.all())
        for purchase in purchases
    ))
    
    # Comparativa con periodo anterior
    if period == 'month':
        prev_start = (first_day_month - timedelta(days=1)).replace(day=1)
        prev_end = first_day_month - timedelta(days=1)
    else:
        prev_start = start_date - (today - start_date)
        prev_end = start_date - timedelta(days=1)
    
    prev_purchases = PurchaseOrder.objects.filter(
        status__symbol__in=['RECEIVED', 'CLOSED'],
        created_at__gte=prev_start,
        created_at__lte=prev_end
    )
    
    prev_total = float(sum(
        sum(Decimal(str(line.quantity)) * line.price for line in purchase.lines.all())
        for purchase in prev_purchases
    ))
    
    if prev_total > 0:
        growth_percentage = ((total_purchases - prev_total) / prev_total) * 100
    else:
        growth_percentage = 100 if total_purchases > 0 else 0
    
    context = {
        'purchases': purchases,
        'period': period,
        'supplier_analysis': supplier_analysis[:10],  # Top 10
        'top_materials': top_materials,
        'total_purchases': total_purchases,
        'purchases_count': purchases.count(),
        'prev_total': prev_total,
        'growth_percentage': growth_percentage,
        'suppliers': Supplier.objects.all(),
        'selected_supplier': supplier_id,
    }
    
    return render(request, 'reporting/purchases_report.html', context)


@login_required
def inventory_report(request):
    """Vista detallada de reporte de inventario"""
    from materials.models import Material
    from inventory.models import InventoryLocation
    
    # Calcular stock actual por material
    materials_stock = []
    
    for material in Material.objects.all():
        # Entradas
        total_in = InventoryMovement.objects.filter(
            material=material,
            movement_type__symbol__endswith='_IN'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        # Salidas
        total_out = InventoryMovement.objects.filter(
            material=material,
            movement_type__symbol__endswith='_OUT'
        ).aggregate(total=Sum('quantity'))['total'] or 0
        
        current_stock = total_in - total_out
        
        materials_stock.append({
            'material': material,
            'stock': current_stock,
            'unit': material.unit_measure.symbol if material.unit_measure else 'UND',
        })
    
    context = {
        'materials_stock': materials_stock,
        'locations': InventoryLocation.objects.all(),
    }
    
    return render(request, 'reporting/inventory_report.html', context)


@login_required
def accounting_report(request):
    """Vista detallada de reporte contable"""
    # Asientos del mes actual
    today = timezone.now().date()
    first_day_month = today.replace(day=1)
    
    entries = JournalEntry.objects.filter(
        date__gte=first_day_month,
        status='POSTED'
    ).select_related('currency').prefetch_related('lines__account')
    
    # Totales
    total_debit = sum(e.get_total_debit() for e in entries)
    total_credit = sum(e.get_total_credit() for e in entries)
    
    context = {
        'entries': entries,
        'total_debit': total_debit,
        'total_credit': total_credit,
        'period': first_day_month.strftime('%B %Y'),
    }
    
    return render(request, 'reporting/accounting_report.html', context)
