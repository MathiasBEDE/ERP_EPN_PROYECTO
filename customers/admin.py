from django.contrib import admin
from .models import Customer

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id_customer', 'name', 'country', 'category', 'status']
    list_filter = ['country', 'category', 'status']
    search_fields = ['id_customer', 'name', 'legal_name', 'email']
