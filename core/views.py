from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from users.models import UserRole, Role

def index(request):
    from django.http import HttpResponse
    return HttpResponse("ERP CORE funcionando correctamente.")

@login_required
def dashboard_view(request):
    user = request.user
    
    permissions = {
        "materials": 0,
        "customers": 0,
        "suppliers": 0,
        "purchases": 0,
        "sales": 0,
        "inventory": 0,
        "accounting": 0,
        "reporting": 0,
    }
    
    roles = []
    
    for user_role in UserRole.objects.select_related("role").filter(user=user):
        role = user_role.role
        roles.append(role.role_name)
        permissions["materials"] = max(permissions["materials"], getattr(role, 'materials', 0))
        permissions["customers"] = max(permissions["customers"], getattr(role, 'customers', 0))
        permissions["suppliers"] = max(permissions["suppliers"], getattr(role, 'suppliers', 0))
        permissions["purchases"] = max(permissions["purchases"], getattr(role, 'purchases', 0))
        permissions["sales"] = max(permissions["sales"], getattr(role, 'sales', 0))
        permissions["inventory"] = max(permissions["inventory"], getattr(role, 'inventory', 0))
        permissions["accounting"] = max(permissions["accounting"], getattr(role, 'accounting', 0))
        permissions["reporting"] = max(permissions["reporting"], getattr(role, 'reporting', 0))
    
    context = {
        "user": user,
        "permissions": permissions,
        "roles": roles,
    }
    
    return render(request, "core/dashboard.html", context)
