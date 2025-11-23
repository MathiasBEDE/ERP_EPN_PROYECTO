from django.urls import path
from . import views
from .api import views as api_views

app_name = 'reporting'

urlpatterns = [
    # Vistas HTML
    path('dashboard/', views.dashboard, name='dashboard'),
    path('sales/', views.sales_report, name='sales_report'),
    path('purchases/', views.purchases_report, name='purchases_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('accounting/', views.accounting_report, name='accounting_report'),
    
    # API Endpoints
    path('api/income/monthly/', api_views.monthly_income_api, name='api_monthly_income'),
    path('api/expenses/monthly/', api_views.monthly_expenses_api, name='api_monthly_expenses'),
    path('api/inventory/value/', api_views.inventory_value_api, name='api_inventory_value'),
    path('api/sales/trend/', api_views.sales_trend_api, name='api_sales_trend'),
    path('api/metrics/summary/', api_views.metrics_summary_api, name='api_metrics_summary'),
]
