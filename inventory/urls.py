from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_dashboard, name='inventory_dashboard'),
    path('movements/', views.inventory_movement_list_view, name='inventory_movement_list'),
    path('stock/', views.inventory_stock_view, name='inventory_stock'),
    path('adjustment/new/', views.inventory_adjustment_view, name='inventory_adjustment'),
]
