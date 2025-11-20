from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from users.models import User
from core.models import Status, Currency, Country


class AccountNature(models.Model):
    id_account_nature = models.CharField(max_length=50, unique=True, verbose_name="Account Nature ID", default='AN001')
    name = models.CharField(max_length=100, unique=True)
    symbol = models.CharField(max_length=10, unique=True)
    effect_on_balance = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "account_nature"
        verbose_name = "Account Nature"
        verbose_name_plural = "Account Natures"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.id_account_nature} - {self.name} ({self.symbol})"

class AccountGroup(models.Model):
    id_account_group = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    code_prefix = models.CharField(max_length=20)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "account_group"
        verbose_name = "Account Group"
        verbose_name_plural = "Account Groups"
        ordering = ['name']
    
    def __str__(self):
        return f"{self.code_prefix} - {self.name}"

class AccountType(models.Model):
    id_account_type = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "account_type"
        verbose_name = "Account Type"
        verbose_name_plural = "Account Types"
        ordering = ['name']
    
    def __str__(self):
        return self.name

class AccountAccount(models.Model):
    id_account = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    account_type = models.ForeignKey(AccountType, on_delete=models.PROTECT)
    account_group = models.ForeignKey(AccountGroup, on_delete=models.PROTECT)
    nature = models.ForeignKey(AccountNature, on_delete=models.PROTECT)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT)
    country = models.ForeignKey(Country, on_delete=models.PROTECT)
    is_control_account = models.BooleanField(default=False)
    parent_account = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_accounts')
    status = models.ForeignKey(Status, on_delete=models.PROTECT, default=1)
    
    # Campo para saldos actualizados automáticamente - útil para reportes financieros
    current_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="Saldo Actual",
        help_text="Saldo actual de la cuenta (actualizado automáticamente al contabilizar asientos)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "account_account"
        verbose_name = "Account"
        verbose_name_plural = "Accounts"
        ordering = ['code']
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class JournalEntry(models.Model):
    """
    Modelo para representar un asiento contable (journal entry).
    Registra las transacciones contables del sistema con sus líneas de débito y crédito.
    """
    
    # Choices para operation_type
    OPERATION_TYPE_CHOICES = [
        ('PURCHASE', 'Compra'),
        ('SALE', 'Venta'),
        ('PRODUCTION', 'Producción'),
        ('ADJUSTMENT', 'Ajuste de Inventario'),
        ('TRANSFER', 'Transferencia'),
        ('MANUAL', 'Manual'),
    ]
    
    # Choices para module
    MODULE_CHOICES = [
        ('PURCHASES', 'Compras'),
        ('SALES', 'Ventas'),
        ('MANUFACTURING', 'Manufactura'),
        ('INVENTORY', 'Inventario'),
        ('ACCOUNTING', 'Contabilidad'),
    ]
    
    # Choices para status
    STATUS_CHOICES = [
        ('DRAFT', 'Borrador'),
        ('POSTED', 'Contabilizado'),
        ('CANCELLED', 'Anulado'),
    ]
    
    id_journal_entry = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Journal Entry ID",
        help_text="Identificador único del asiento contable (ej: JE-000001)"
    )
    date = models.DateField(
        verbose_name="Fecha",
        help_text="Fecha del asiento contable"
    )
    description = models.TextField(
        verbose_name="Descripción",
        help_text="Descripción general del asiento contable"
    )
    operation_type = models.CharField(
        max_length=50,
        choices=OPERATION_TYPE_CHOICES,
        verbose_name="Tipo de Operación",
        help_text="Tipo de operación que genera el asiento"
    )
    reference = models.CharField(
        max_length=100,
        verbose_name="Referencia",
        help_text="ID del documento origen (ej: PO-0001, SO-0001, WO-0001, etc.)"
    )
    module = models.CharField(
        max_length=50,
        choices=MODULE_CHOICES,
        verbose_name="Módulo",
        help_text="Módulo del sistema que genera el asiento"
    )
    currency = models.ForeignKey(
        Currency,
        on_delete=models.PROTECT,
        related_name='journal_entries',
        verbose_name="Moneda",
        help_text="Moneda del asiento contable"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('DRAFT', 'Borrador'),
            ('POSTED', 'Contabilizado'),
            ('CANCELLED', 'Anulado'),
        ],
        default='DRAFT',
        verbose_name="Estado",
        help_text="Estado del asiento contable"
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado el"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Actualizado el"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_journal_entries',
        verbose_name="Creado por"
    )
    
    class Meta:
        db_table = 'journal_entry'
        verbose_name = 'Asiento Contable'
        verbose_name_plural = 'Asientos Contables'
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['id_journal_entry']),
            models.Index(fields=['date']),
            models.Index(fields=['operation_type']),
            models.Index(fields=['module']),
            models.Index(fields=['reference']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.id_journal_entry} - {self.date} - {self.get_operation_type_display()}"
    
    @staticmethod
    def generate_journal_entry_id():
        """
        Genera el siguiente ID de asiento contable secuencial.
        Formato: JE-000001, JE-000002, etc.
        """
        last_entry = JournalEntry.objects.order_by('-id_journal_entry').first()
        if last_entry:
            last_number = int(last_entry.id_journal_entry.split('-')[1])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"JE-{new_number:06d}"
    
    def get_total_debit(self):
        """
        Calcula el total de débitos del asiento.
        """
        from decimal import Decimal
        return sum(line.debit for line in self.lines.all()) or Decimal('0.00')
    
    def get_total_credit(self):
        """
        Calcula el total de créditos del asiento.
        """
        from decimal import Decimal
        return sum(line.credit for line in self.lines.all()) or Decimal('0.00')
    
    def is_balanced(self):
        """
        Verifica si el asiento está balanceado (débitos = créditos).
        """
        return self.get_total_debit() == self.get_total_credit()
    
    def clean(self):
        """
        Validación del modelo a nivel de asiento.
        """
        super().clean()
        
        # Validar que el asiento esté balanceado antes de contabilizar
        if self.status == 'POSTED' and not self.is_balanced():
            raise ValidationError(
                'El asiento no está balanceado. Los débitos deben ser iguales a los créditos.'
            )
    
    def post(self):
        """
        Contabiliza el asiento (cambia estado a POSTED).
        """
        if not self.is_balanced():
            raise ValidationError('No se puede contabilizar un asiento desbalanceado.')
        
        self.status = 'POSTED'
        self.save()
    
    def cancel(self):
        """
        Anula el asiento (cambia estado a CANCELLED).
        """
        self.status = 'CANCELLED'
        self.save()


class JournalEntryLine(models.Model):
    """
    Modelo para representar una línea de asiento contable.
    Cada línea contiene una cuenta con su débito o crédito.
    """
    
    journal_entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='lines',
        verbose_name="Asiento Contable",
        help_text="Asiento contable al que pertenece esta línea"
    )
    account = models.ForeignKey(
        AccountAccount,
        on_delete=models.PROTECT,
        related_name='journal_entry_lines',
        verbose_name="Cuenta",
        help_text="Cuenta contable afectada"
    )
    description = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Descripción",
        help_text="Descripción específica de esta línea (opcional)"
    )
    debit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Débito",
        help_text="Monto del débito"
    )
    credit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="Crédito",
        help_text="Monto del crédito"
    )
    position = models.IntegerField(
        verbose_name="Posición",
        help_text="Orden de la línea en el asiento"
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Creado el"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Actualizado el"
    )
    
    class Meta:
        db_table = 'journal_entry_line'
        verbose_name = 'Línea de Asiento Contable'
        verbose_name_plural = 'Líneas de Asiento Contable'
        ordering = ['journal_entry', 'position']
        indexes = [
            models.Index(fields=['journal_entry']),
            models.Index(fields=['account']),
        ]
        unique_together = [['journal_entry', 'position']]
    
    def __str__(self):
        amount = self.debit if self.debit > 0 else self.credit
        type_str = "Débito" if self.debit > 0 else "Crédito"
        return f"{self.account.code} - {type_str}: {amount}"
    
    def clean(self):
        """
        Validación del modelo a nivel de línea.
        """
        super().clean()
        
        from decimal import Decimal
        
        # Convertir a Decimal para comparación precisa
        debit = Decimal(str(self.debit))
        credit = Decimal(str(self.credit))
        
        # No permitir ambos débito y crédito > 0
        if debit > 0 and credit > 0:
            raise ValidationError(
                'Una línea no puede tener débito y crédito al mismo tiempo. '
                'Debe tener uno de los dos en 0.'
            )
        
        # Al menos uno debe ser > 0
        if debit == 0 and credit == 0:
            raise ValidationError(
                'Una línea debe tener débito o crédito mayor a 0.'
            )
        
        # No permitir valores negativos
        if debit < 0 or credit < 0:
            raise ValidationError(
                'Los valores de débito y crédito no pueden ser negativos.'
            )

