from django.contrib import admin
from .models import Status, Currency, Country

# Registra tus modelos aquí.

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol']
    search_fields = ['code', 'name']

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    search_fields = ['code', 'name']
