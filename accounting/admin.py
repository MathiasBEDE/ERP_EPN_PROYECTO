from django.contrib import admin
from .models import (
    AccountNature, AccountGroup, AccountType, AccountAccount,
    JournalEntry, JournalEntryLine
)


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


# ==================== JOURNAL ENTRY ADMINISTRATION ====================

class JournalEntryLineInline(admin.TabularInline):
    """
    Inline para administrar líneas de asiento contable.
    """
    model = JournalEntryLine
    extra = 2
    fields = ['position', 'account', 'description', 'debit', 'credit']
    ordering = ['position']


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    """
    Administrador para asientos contables con sus líneas.
    """
    list_display = [
        'id_journal_entry', 
        'date', 
        'operation_type', 
        'reference', 
        'module', 
        'currency',
        'status',
        'is_balanced_display',
        'created_at'
    ]
    list_filter = [
        'date', 
        'operation_type', 
        'module', 
        'status',
        'currency',
        'created_at'
    ]
    search_fields = [
        'id_journal_entry', 
        'reference', 
        'description'
    ]
    readonly_fields = [
        'id_journal_entry',
        'created_at', 
        'updated_at', 
        'created_by',
        'get_total_debit',
        'get_total_credit',
        'is_balanced_display'
    ]
    inlines = [JournalEntryLineInline]
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Información del Asiento', {
            'fields': (
                'id_journal_entry',
                'date',
                'description',
                'status'
            )
        }),
        ('Origen del Asiento', {
            'fields': (
                'operation_type',
                'module',
                'reference'
            )
        }),
        ('Información Financiera', {
            'fields': (
                'currency',
                'get_total_debit',
                'get_total_credit',
                'is_balanced_display'
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_at',
                'updated_at',
                'created_by'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        Genera automáticamente el ID del asiento si es nuevo.
        """
        if not change:  # Si es un nuevo asiento
            if not obj.id_journal_entry:
                obj.id_journal_entry = JournalEntry.generate_journal_entry_id()
            if not obj.created_by:
                obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def is_balanced_display(self, obj):
        """
        Muestra si el asiento está balanceado.
        """
        if obj.pk:
            is_balanced = obj.is_balanced()
            if is_balanced:
                return "✅ Balanceado"
            else:
                return "❌ Desbalanceado"
        return "-"
    is_balanced_display.short_description = 'Balance'
    
    def get_total_debit(self, obj):
        """
        Muestra el total de débitos.
        """
        if obj.pk:
            return f"{obj.get_total_debit():.2f}"
        return "0.00"
    get_total_debit.short_description = 'Total Débito'
    
    def get_total_credit(self, obj):
        """
        Muestra el total de créditos.
        """
        if obj.pk:
            return f"{obj.get_total_credit():.2f}"
        return "0.00"
    get_total_credit.short_description = 'Total Crédito'


@admin.register(JournalEntryLine)
class JournalEntryLineAdmin(admin.ModelAdmin):
    """
    Administrador para líneas individuales de asiento contable.
    """
    list_display = [
        'journal_entry', 
        'position', 
        'account', 
        'debit', 
        'credit',
        'created_at'
    ]
    list_filter = [
        'journal_entry__date',
        'account__account_type',
        'created_at'
    ]
    search_fields = [
        'journal_entry__id_journal_entry',
        'account__code',
        'account__name',
        'description'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Información de la Línea', {
            'fields': (
                'journal_entry',
                'position',
                'account',
                'description'
            )
        }),
        ('Montos', {
            'fields': (
                'debit',
                'credit'
            )
        }),
        ('Auditoría', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )

