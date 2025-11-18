from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    # Vista de lista de órdenes
    path('purchase-order/', views.purchase_order_list_view, name='purchase_order_list'),
    
    # Vista del formulario HTML
    path('purchase-order/new/', views.purchase_order_form_view, name='purchase_order_new'),
    
    # Vista de detalle de orden
    path('purchase-order/<str:order_id>/', views.purchase_order_detail_view, name='purchase_order_detail'),
    
    # APIs
    path('api/supplier/details/<str:supplier_id>/', views.supplier_detail_api, name='supplier_detail_api'),
    path('api/material/details/<str:material_id>/', views.material_detail_api, name='material_detail_api'),
    path('api/purchase-order/create/', views.create_purchase_order_api, name='purchase_order_create_api'),
]
