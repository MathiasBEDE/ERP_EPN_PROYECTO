from django.contrib import admin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Role, UserRole

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("username", "email")

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("role_name", "materials", "customers", "suppliers", "purchases", "sales", "inventory", "accounting", "reporting")
    list_filter = ("materials", "customers", "suppliers", "purchases", "sales", "inventory", "accounting", "reporting")
    search_fields = ("role_name",)

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "role")
    list_filter = ("role",)
    search_fields = ("user__username", "role__role_name")
