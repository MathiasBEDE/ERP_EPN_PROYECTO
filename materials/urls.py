from django.urls import path
from . import views

app_name = 'materials'

urlpatterns = [
    path('', views.materials_list, name='materials_list'),
    path('create/', views.material_create, name='material_create'),
    path('<int:id>/edit/', views.material_edit, name='material_edit'),
    path('<int:id>/delete/', views.material_delete, name='material_delete'),
    path('bulk-upload/', views.material_bulk_upload, name='material_bulk_upload'),
    path('bulk-upload/template/', views.download_template_materials, name='download_template_materials'),
]


