from django.urls import path
from . import views

app_name = 'suppliers'

urlpatterns = [
    path('', views.suppliers_list, name='suppliers_list'),
    path('create/', views.supplier_create, name='supplier_create'),
    path('<int:id>/edit/', views.supplier_edit, name='supplier_edit'),
    path('<int:id>/delete/', views.supplier_delete, name='supplier_delete'),
    path('bulk-upload/', views.supplier_bulk_upload, name='supplier_bulk_upload'),
    path('bulk-upload/template/', views.download_template_suppliers, name='download_template_suppliers'),
]
