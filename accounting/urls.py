"""
URLs para el módulo de Contabilidad (Accounting).
"""

from django.urls import path
from . import views

app_name = 'accounting'

urlpatterns = [
    # Listado de asientos contables
    path('journal-entries/', views.journal_entry_list_view, name='journal_entry_list'),
    
    # Detalle de asiento contable
    path('journal-entries/<str:id_journal_entry>/', views.journal_entry_detail_view, name='journal_entry_detail'),
]
