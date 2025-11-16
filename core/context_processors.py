from users.models import UserRole

def user_permissions(request):
    """
    Context processor que retorna los permisos del usuario
    para todos los módulos del ERP.
    """
    if not request.user.is_authenticated:
        return {
            'perms': {
                'materials': 0,
                'customers': 0,
                'suppliers': 0,
                'purchases': 0,
                'sales': 0,
                'inventory': 0,
                'accounting': 0,
                'reporting': 0,
            }
        }
    
    user = request.user
    
    permissions = {
        'materials': 0,
        'customers': 0,
        'suppliers': 0,
        'purchases': 0,
        'sales': 0,
        'inventory': 0,
        'accounting': 0,
        'reporting': 0,
    }
    
    user_roles = UserRole.objects.select_related('role').filter(user=user)
    
    for user_role in user_roles:
        role = user_role.role
        permissions['materials'] = max(permissions['materials'], getattr(role, 'materials', 0))
        permissions['customers'] = max(permissions['customers'], getattr(role, 'customers', 0))
        permissions['suppliers'] = max(permissions['suppliers'], getattr(role, 'suppliers', 0))
        permissions['purchases'] = max(permissions['purchases'], getattr(role, 'purchases', 0))
        permissions['sales'] = max(permissions['sales'], getattr(role, 'sales', 0))
        permissions['inventory'] = max(permissions['inventory'], getattr(role, 'inventory', 0))
        permissions['accounting'] = max(permissions['accounting'], getattr(role, 'accounting', 0))
        permissions['reporting'] = max(permissions['reporting'], getattr(role, 'reporting', 0))
    
    return {'perms': permissions}
