from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.customers_list, name='customers_list'),
    path('create/', views.customer_create, name='customer_create'),
    path('<int:id>/edit/', views.customer_edit, name='customer_edit'),
    path('<int:id>/delete/', views.customer_delete, name='customer_delete'),
    path('bulk-upload/', views.customer_bulk_upload, name='customer_bulk_upload'),
    path('bulk-upload/template/', views.download_template_customers, name='download_template_customers'),
]
