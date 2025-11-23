from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from sales.models import SalesOrder
from purchases.models import PurchaseOrder
from accounting.models import JournalEntry
from inventory.models import InventoryMovement
from manufacturing.models import WorkOrder


@login_required
def monthly_income_api(request):
    """
    API: Ingresos mensuales de los últimos 6 meses.
    Basado en ventas completadas y asientos de ingreso.
    
    Returns:
        JSON con meses y valores de ingreso
    """
    try:
        # Calcular últimos 6 meses
        today = timezone.now().date()
        months_data = []
        
        for i in range(5, -1, -1):  # 6 meses hacia atrás
            month_date = today - timedelta(days=30*i)
            first_day = month_date.replace(day=1)
            
            # Último día del mes
            if month_date.month == 12:
                last_day = month_date.replace(day=31)
            else:
                next_month = month_date.replace(month=month_date.month + 1, day=1)
                last_day = next_month - timedelta(days=1)
            
            # Calcular ingresos desde ventas (suma de totales)
            sales_income = 0
            sales = SalesOrder.objects.filter(
                status__symbol='DELIVERED',
                issue_date__gte=first_day,
                issue_date__lte=last_day
            ).prefetch_related('lines')
            
            for sale in sales:
                sale_total = sum(
                    Decimal(str(line.quantity)) * line.price 
                    for line in sale.lines.all()
                )
                sales_income += float(sale_total)
            
            months_data.append({
                'month': first_day.strftime('%B'),
                'year': first_day.year,
                'income': round(sales_income, 2)
            })
        
        return JsonResponse({
            'success': True,
            'data': months_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def monthly_expenses_api(request):
    """
    API: Egresos mensuales de los últimos 6 meses.
    Basado en compras recibidas.
    
    Returns:
        JSON con meses y valores de egreso
    """
    try:
        today = timezone.now().date()
        months_data = []
        
        for i in range(5, -1, -1):
            month_date = today - timedelta(days=30*i)
            first_day = month_date.replace(day=1)
            
            if month_date.month == 12:
                last_day = month_date.replace(day=31)
            else:
                next_month = month_date.replace(month=month_date.month + 1, day=1)
                last_day = next_month - timedelta(days=1)
            
            # Calcular egresos desde compras
            purchases_expense = 0
            purchases = PurchaseOrder.objects.filter(
                status__symbol__in=['RECEIVED', 'CLOSED'],
                created_at__gte=first_day,
                created_at__lte=last_day
            ).prefetch_related('lines')
            
            for purchase in purchases:
                purchase_total = sum(
                    Decimal(str(line.quantity)) * line.price 
                    for line in purchase.lines.all()
                )
                purchases_expense += float(purchase_total)
            
            months_data.append({
                'month': first_day.strftime('%B'),
                'year': first_day.year,
                'expenses': round(purchases_expense, 2)
            })
        
        return JsonResponse({
            'success': True,
            'data': months_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def inventory_value_api(request):
    """
    API: Valor total del inventario actual.
    Calcula stock actual y estima valor.
    
    Returns:
        JSON con valor total de inventario
    """
    try:
        from materials.models import Material
        
        total_value = 0
        materials_detail = []
        
        for material in Material.objects.all():
            # Calcular stock actual
            total_in = InventoryMovement.objects.filter(
                material=material,
                movement_type__symbol__endswith='_IN'
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            total_out = InventoryMovement.objects.filter(
                material=material,
                movement_type__symbol__endswith='_OUT'
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            current_stock = total_in - total_out
            
            # Estimar valor (precio promedio * stock)
            # TODO: Implementar costo promedio real
            estimated_unit_price = 50.00
            material_value = current_stock * estimated_unit_price
            total_value += material_value
            
            if current_stock > 0:
                materials_detail.append({
                    'material': material.name,
                    'stock': float(current_stock),
                    'unit_value': estimated_unit_price,
                    'total_value': round(material_value, 2)
                })
        
        return JsonResponse({
            'success': True,
            'total_value': round(total_value, 2),
            'materials': materials_detail
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def sales_trend_api(request):
    """
    API: Tendencia de ventas (últimos 30 días).
    
    Returns:
        JSON con ventas por día
    """
    try:
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        
        sales_by_day = []
        
        for i in range(30):
            day = thirty_days_ago + timedelta(days=i)
            
            sales_count = SalesOrder.objects.filter(
                status__symbol='DELIVERED',
                issue_date=day
            ).count()
            
            sales_by_day.append({
                'date': day.strftime('%Y-%m-%d'),
                'count': sales_count
            })
        
        return JsonResponse({
            'success': True,
            'data': sales_by_day
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
def metrics_summary_api(request):
    """
    API: Resumen de métricas principales del ERP.
    
    Returns:
        JSON con todas las métricas clave
    """
    try:
        today = timezone.now().date()
        first_day_month = today.replace(day=1)
        
        # Ventas del mes
        sales_count = SalesOrder.objects.filter(
            status__symbol='DELIVERED',
            issue_date__gte=first_day_month
        ).count()
        
        sales_total = 0
        for sale in SalesOrder.objects.filter(status__symbol='DELIVERED', issue_date__gte=first_day_month):
            sale_total = sum(
                Decimal(str(line.quantity)) * line.price 
                for line in sale.lines.all()
            )
            sales_total += float(sale_total)
        
        # Compras del mes
        purchases_count = PurchaseOrder.objects.filter(
            status__symbol__in=['RECEIVED', 'CLOSED'],
            created_at__gte=first_day_month
        ).count()
        
        purchases_total = 0
        for purchase in PurchaseOrder.objects.filter(status__symbol__in=['RECEIVED', 'CLOSED'], created_at__gte=first_day_month):
            purchase_total = sum(
                Decimal(str(line.quantity)) * line.price 
                for line in purchase.lines.all()
            )
            purchases_total += float(purchase_total)
        
        # Producción del mes
        production_count = WorkOrder.objects.filter(
            created_at__gte=first_day_month
        ).count()
        
        # Asientos contables del mes
        journal_entries_count = JournalEntry.objects.filter(
            date__gte=first_day_month
        ).count()
        
        # Cálculo de beneficio neto
        net_profit = sales_total - purchases_total
        
        return JsonResponse({
            'success': True,
            'period': first_day_month.strftime('%B %Y'),
            'metrics': {
                'sales': {
                    'count': sales_count,
                    'total': round(sales_total, 2)
                },
                'purchases': {
                    'count': purchases_count,
                    'total': round(purchases_total, 2)
                },
                'production': {
                    'count': production_count
                },
                'journal_entries': {
                    'count': journal_entries_count
                },
                'net_profit': round(net_profit, 2)
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
