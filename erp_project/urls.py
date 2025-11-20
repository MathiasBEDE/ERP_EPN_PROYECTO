"""
Configuración de URLs para el proyecto erp_project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('', include('core.urls')),
    path('materials/', include('materials.urls', namespace='materials')),
    path('suppliers/', include('suppliers.urls', namespace='suppliers')),
    path('customers/', include('customers.urls', namespace='customers')),
    path('purchases/', include('purchases.urls', namespace='purchases')),
    path('inventory/', include('inventory.urls', namespace='inventory')),
    path('manufacturing/', include('manufacturing.urls', namespace='manufacturing')),
    path('sales/', include('sales.urls', namespace='sales')),
    path('accounting/', include('accounting.urls', namespace='accounting')),
]
