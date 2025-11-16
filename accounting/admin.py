from django.contrib import admin
from .models import AccountNature, AccountGroup, AccountType, AccountAccount

@admin.register(AccountNature)
class AccountNatureAdmin(admin.ModelAdmin):
    list_display = ['id_account_nature', 'name', 'symbol', 'effect_on_balance', 'created_by']
    search_fields = ['id_account_nature', 'name', 'symbol']
    fields = ['id_account_nature', 'name', 'symbol', 'effect_on_balance', 'created_by']

@admin.register(AccountGroup)
class AccountGroupAdmin(admin.ModelAdmin):
    list_display = ['id_account_group', 'name', 'code_prefix']
    search_fields = ['name', 'code_prefix']

@admin.register(AccountType)
class AccountTypeAdmin(admin.ModelAdmin):
    list_display = ['id_account_type', 'name']
    search_fields = ['name']

@admin.register(AccountAccount)
class AccountAccountAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'account_type', 'account_group', 'nature', 'is_control_account', 'status']
    list_filter = ['account_type', 'account_group', 'nature', 'is_control_account', 'status', 'country']
    search_fields = ['code', 'name']
