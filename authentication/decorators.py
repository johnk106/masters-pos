from functools import wraps
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden


def has_role(role_name):
    """
    Decorator to check if user has a specific role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('authentication:login')
            
            # Superuser has access to everything
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check if user has the required role
            try:
                user_role = request.user.userprofile.role
                if user_role and user_role.name == role_name:
                    return view_func(request, *args, **kwargs)
            except:
                pass
            
            messages.error(request, f"Access denied. You need '{role_name}' role to access this page.")
            return redirect('landing:homepage')
        
        return wrapper
    return decorator


def has_any_role(role_names):
    """
    Decorator to check if user has any of the specified roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('authentication:login')
            
            # Superuser has access to everything
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check if user has any of the required roles
            try:
                user_role = request.user.userprofile.role
                if user_role and user_role.name in role_names:
                    return view_func(request, *args, **kwargs)
            except:
                pass
            
            roles_str = ', '.join(role_names)
            messages.error(request, f"Access denied. You need one of these roles: {roles_str}")
            return redirect('landing:homepage')
        
        return wrapper
    return decorator


def has_permission(permission_codename):
    """
    Decorator to check if user has a specific permission through their role.
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('authentication:login')
            
            # Superuser has access to everything
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            
            # Check if user has the required permission through their role
            try:
                user_role = request.user.userprofile.role
                if user_role and user_role.permissions.filter(codename=permission_codename).exists():
                    return view_func(request, *args, **kwargs)
            except:
                pass
            
            messages.error(request, f"Access denied. You don't have permission to access this page.")
            return redirect('landing:homepage')
        
        return wrapper
    return decorator


def admin_or_manager_required(view_func):
    """
    Decorator that allows only Admin or Manager roles.
    """
    return has_any_role(['Admin', 'Manager'])(view_func)


def admin_only(view_func):
    """
    Decorator that allows only Admin role.
    """
    return has_role('Admin')(view_func)


def manager_or_above(view_func):
    """
    Decorator that allows Admin, Manager, or Supervisor roles.
    """
    return has_any_role(['Admin', 'Manager', 'Supervisor'])(view_func)


# Middleware for role-based access control
class RoleBasedAccessMiddleware:
    """
    Middleware to enforce role-based access control on specific URL patterns.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Define URL patterns and required roles
        self.url_role_map = {
            '/authentication/users/': ['Admin', 'Manager'],
            '/authentication/roles/': ['Admin'],
            '/inventory/': ['Admin', 'Manager', 'Inventory Manager', 'Store Keeper'],
            '/sales/': ['Admin', 'Manager', 'Salesman'],
            '/purchases/': ['Admin', 'Manager', 'Supervisor'],
            '/finance/': ['Admin', 'Manager'],
            '/people/': ['Admin', 'Manager'],
        }

    def __call__(self, request):
        # Check if user is authenticated
        if request.user.is_authenticated and not request.user.is_superuser:
            # Check URL patterns
            for url_pattern, required_roles in self.url_role_map.items():
                if request.path.startswith(url_pattern):
                    try:
                        user_role = request.user.userprofile.role
                        if not user_role or user_role.name not in required_roles:
                            messages.error(request, f"Access denied. You need one of these roles: {', '.join(required_roles)}")
                            return redirect('landing:homepage')
                    except:
                        messages.error(request, "Access denied. No role assigned.")
                        return redirect('landing:homepage')
        
        response = self.get_response(request)
        return response