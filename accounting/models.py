from django.db import models
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
