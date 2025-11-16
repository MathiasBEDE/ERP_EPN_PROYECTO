from django.db import models

from django.db import models
from django.contrib.auth.models import AbstractUser

PERMISSION_CHOICES = (
    (0, "Sin acceso"),
    (1, "Solo visualizar"),
    (2, "Leer y escribir")
)

class User(AbstractUser):
    class Meta:
        db_table = "users"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

class Role(models.Model):
    role_name = models.CharField(max_length=100, unique=True)
    materials = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    customers = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    suppliers = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    purchases = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    sales = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    inventory = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    accounting = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    reporting = models.IntegerField(choices=PERMISSION_CHOICES, default=0)
    
    class Meta:
        db_table = "roles"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
    
    def __str__(self):
        return self.role_name

class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_roles")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="user_roles")
    
    class Meta:
        db_table = "users_roles"
        verbose_name = "Rol de usuario"
        verbose_name_plural = "Roles de usuarios"
        unique_together = ("user", "role")
    
    def __str__(self):
        return f"{self.user.username} - {self.role.role_name}"
