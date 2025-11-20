from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Vistas principales
    path('sales-order/', views.sales_order_list_view, name='sales_order_list'),
    path('sales-order/new/', views.sales_order_create_view, name='sales_order_new'),
    path('sales-order/<str:order_id>/', views.sales_order_detail_view, name='sales_order_detail'),
    path('sales-order/<str:order_id>/edit/', views.sales_order_edit_view, name='sales_order_edit'),
    
    # APIs
    path('api/customer/<str:customer_id>/', views.customer_detail_api, name='customer_detail_api'),
    path('api/material/<str:material_id>/', views.material_detail_api, name='material_detail_api'),
    path('api/create/', views.create_sales_order_api, name='create_sales_order_api'),
]
