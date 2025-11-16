from django.db import models
from users.models import User
from suppliers.models import PaymentMethod

class Customer(models.Model):
    id_customer = models.CharField(max_length=50, unique=True)
    legal_name = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    tax_id = models.CharField(max_length=50)
    country = models.CharField(max_length=100)
    state_province = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=300)
    zip_code = models.IntegerField()
    phone = models.IntegerField()
    email = models.EmailField()
    contact_name = models.CharField(max_length=200)
    contact_role = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    payment_terms = models.CharField(max_length=100)
    currency = models.CharField(max_length=10)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, default=1, verbose_name="Payment Method")
    bank_account = models.CharField(max_length=100)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        db_table = "customers"
        verbose_name = "Customer"
        verbose_name_plural = "Customers"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.id_customer} - {self.name}"
