from django.urls import path
from manufacturing import views

app_name = 'manufacturing'
urlpatterns = [
    path('work-order/', views.work_order_list_view, name='work_order_list'),
    path('work-order/new/', views.work_order_form_view, name='work_order_new'),
    path('work-order/<str:wo_id>/', views.work_order_detail_view, name='work_order_detail'),  # detalle (opcional)
]
