"""
Security Audit Script for Django Admin Project
Scans all URL patterns and views to ensure proper role-based protection.
"""

import os
import sys
import django
import importlib
import inspect
import re
from django.conf import settings
from django.urls import get_resolver
from django.core.management.base import BaseCommand
from django.test import TestCase
from django.contrib.auth.models import User
from authentication.models import Role, UserProfile
from authentication.decorators import (
    has_role, has_any_role, has_permission, 
    admin_only, manager_or_above, admin_or_manager_required
)

class SecurityAudit:
    """Main security audit class"""
    
    def __init__(self):
        self.unprotected_views = []
        self.protected_views = []
        self.protection_decorators = [
            'has_role', 'has_any_role', 'has_permission',
            'admin_only', 'manager_or_above', 'admin_or_manager_required',
            'login_required', 'permission_required', 'user_passes_test'
        ]
        self.sensitive_patterns = [
            r'.*admin.*', r'.*manage.*', r'.*delete.*', r'.*create.*',
            r'.*edit.*', r'.*update.*', r'.*report.*', r'.*finance.*',
            r'.*user.*', r'.*role.*', r'.*permission.*'
        ]
    
    def get_all_url_patterns(self, resolver=None, namespace='', prefix=''):
        """Recursively get all URL patterns from the project"""
        if resolver is None:
            resolver = get_resolver()
        
        patterns = []
        
        for pattern in resolver.url_patterns:
            if hasattr(pattern, 'url_patterns'):
                # This is an include() pattern
                new_namespace = namespace
                if hasattr(pattern, 'namespace') and pattern.namespace:
                    new_namespace = f"{namespace}:{pattern.namespace}" if namespace else pattern.namespace
                
                new_prefix = prefix + str(pattern.pattern)
                patterns.extend(self.get_all_url_patterns(
                    pattern, new_namespace, new_prefix
                ))
            else:
                # This is a regular URL pattern
                full_pattern = prefix + str(pattern.pattern)
                view_name = self.get_view_name(pattern)
                view_func = self.get_view_function(pattern)
                
                patterns.append({
                    'pattern': full_pattern,
                    'name': pattern.name,
                    'namespace': namespace,
                    'view_name': view_name,
                    'view_func': view_func,
                    'full_name': f"{namespace}:{pattern.name}" if namespace and pattern.name else pattern.name
                })
        
        return patterns
    
    def get_view_name(self, pattern):
        """Get the view name from a URL pattern"""
        if hasattr(pattern, 'callback'):
            if hasattr(pattern.callback, '__name__'):
                return pattern.callback.__name__
            elif hasattr(pattern.callback, 'view_class'):
                return pattern.callback.view_class.__name__
        return 'Unknown'
    
    def get_view_function(self, pattern):
        """Get the actual view function from a URL pattern"""
        if hasattr(pattern, 'callback'):
            return pattern.callback
        return None
    
    def is_view_protected(self, view_func):
        """Check if a view function has proper protection decorators"""
        if not view_func:
            return False, []
        
        # Check for decorators in the function
        decorators = []
        
        # Check if it's a class-based view
        if hasattr(view_func, 'view_class'):
            view_class = view_func.view_class
            # Check class decorators
            if hasattr(view_class, 'dispatch'):
                decorators.extend(self.get_function_decorators(view_class.dispatch))
            decorators.extend(self.get_class_decorators(view_class))
        else:
            # Function-based view
            decorators.extend(self.get_function_decorators(view_func))
        
        # Check if any protection decorator is present
        protected = any(decorator in self.protection_decorators for decorator in decorators)
        
        return protected, decorators
    
    def get_function_decorators(self, func):
        """Extract decorator names from a function"""
        decorators = []
        
        # Check function attributes for decorators
        if hasattr(func, '__wrapped__'):
            # Function is decorated
            current = func
            while hasattr(current, '__wrapped__'):
                if hasattr(current, '__name__'):
                    # Try to identify decorator by checking common patterns
                    for decorator in self.protection_decorators:
                        if decorator in str(current):
                            decorators.append(decorator)
                current = current.__wrapped__
        
        # Check source code for decorator patterns
        try:
            source = inspect.getsource(func)
            for decorator in self.protection_decorators:
                if f"@{decorator}" in source or f"{decorator}(" in source:
                    decorators.append(decorator)
        except (OSError, TypeError):
            pass
        
        return decorators
    
    def get_class_decorators(self, cls):
        """Extract decorator names from a class"""
        decorators = []
        
        # Check class source for decorators
        try:
            source = inspect.getsource(cls)
            for decorator in self.protection_decorators:
                if f"@{decorator}" in source:
                    decorators.append(decorator)
        except (OSError, TypeError):
            pass
        
        return decorators
    
    def is_sensitive_endpoint(self, pattern, view_name):
        """Check if an endpoint should be considered sensitive"""
        full_string = f"{pattern} {view_name}".lower()
        
        return any(re.search(pattern, full_string) for pattern in self.sensitive_patterns)
    
    def should_be_protected(self, pattern, view_name, namespace):
        """Determine if a view should be protected based on patterns"""
        # Always protect admin views
        if 'admin' in namespace.lower() or 'admin' in view_name.lower():
            return True
        
        # Protect authentication views except login
        if 'authentication' in namespace.lower() and 'login' not in view_name.lower():
            return True
        
        # Protect sensitive endpoints
        if self.is_sensitive_endpoint(pattern, view_name):
            return True
        
        # Protect specific modules
        sensitive_modules = ['finance', 'reports', 'people', 'purchases', 'settings']
        if any(module in namespace.lower() for module in sensitive_modules):
            return True
        
        return False
    
    def audit_views(self):
        """Perform the main security audit"""
        print("Starting Security Audit...")
        print("=" * 50)
        
        patterns = self.get_all_url_patterns()
        
        for pattern_info in patterns:
            pattern = pattern_info['pattern']
            view_name = pattern_info['view_name']
            namespace = pattern_info['namespace'] or ''
            view_func = pattern_info['view_func']
            
            protected, decorators = self.is_view_protected(view_func)
            should_protect = self.should_be_protected(pattern, view_name, namespace)
            
            audit_result = {
                'pattern': pattern,
                'view_name': view_name,
                'namespace': namespace,
                'full_name': pattern_info['full_name'],
                'protected': protected,
                'decorators': decorators,
                'should_protect': should_protect,
                'view_func': view_func
            }
            
            if should_protect and not protected:
                self.unprotected_views.append(audit_result)
            else:
                self.protected_views.append(audit_result)
        
        return self.generate_report()
    
    def generate_report(self):
        """Generate a comprehensive security audit report"""
        report = {
            'total_views': len(self.protected_views) + len(self.unprotected_views),
            'protected_views': len(self.protected_views),
            'unprotected_views': len(self.unprotected_views),
            'unprotected_details': self.unprotected_views,
            'protected_details': self.protected_views,
            'security_score': self.calculate_security_score()
        }
        
        return report
    
    def calculate_security_score(self):
        """Calculate a security score based on protection coverage"""
        total = len(self.protected_views) + len(self.unprotected_views)
        if total == 0:
            return 100
        
        protected_sensitive = sum(1 for view in self.protected_views if view['should_protect'])
        total_sensitive = sum(1 for view in self.unprotected_views if view['should_protect']) + protected_sensitive
        
        if total_sensitive == 0:
            return 100
        
        return (protected_sensitive / total_sensitive) * 100
    
    def print_report(self, report):
        """Print a formatted security audit report"""
        print("\n" + "=" * 50)
        print("SECURITY AUDIT REPORT")
        print("=" * 50)
        
        print(f"Total Views: {report['total_views']}")
        print(f"Protected Views: {report['protected_views']}")
        print(f"Unprotected Views: {report['unprotected_views']}")
        print(f"Security Score: {report['security_score']:.1f}%")
        
        if report['unprotected_views'] > 0:
            print("\n" + "!" * 50)
            print("UNPROTECTED VIEWS REQUIRING ATTENTION:")
            print("!" * 50)
            
            for view in report['unprotected_details']:
                if view['should_protect']:
                    print(f"\n⚠️  {view['namespace']}:{view['view_name']}")
                    print(f"   Pattern: {view['pattern']}")
                    print(f"   Reason: Sensitive endpoint without protection")
        
        print("\n" + "=" * 50)
        print("AUDIT COMPLETE")
        print("=" * 50)
    
    def get_recommended_fixes(self):
        """Get recommended security fixes for unprotected views"""
        fixes = []
        
        for view in self.unprotected_views:
            if not view['should_protect']:
                continue
            
            namespace = view['namespace']
            view_name = view['view_name']
            
            # Determine appropriate decorator based on view type
            if 'admin' in namespace.lower() or 'user' in view_name.lower() or 'role' in view_name.lower():
                decorator = '@admin_only'
            elif 'finance' in namespace.lower() or 'report' in view_name.lower():
                decorator = '@admin_or_manager_required'
            elif 'delete' in view_name.lower() or 'create' in view_name.lower():
                decorator = '@manager_or_above'
            else:
                decorator = '@admin_or_manager_required'
            
            fixes.append({
                'view': view,
                'recommended_decorator': decorator,
                'file_path': self.get_view_file_path(view['view_func'])
            })
        
        return fixes
    
    def get_view_file_path(self, view_func):
        """Get the file path where a view function is defined"""
        if not view_func:
            return "Unknown"
        
        try:
            if hasattr(view_func, 'view_class'):
                return inspect.getfile(view_func.view_class)
            else:
                return inspect.getfile(view_func)
        except (OSError, TypeError):
            return "Unknown"


def run_security_audit():
    """Run the security audit and return results"""
    auditor = SecurityAudit()
    report = auditor.audit_views()
    auditor.print_report(report)
    
    return report, auditor.get_recommended_fixes()


if __name__ == "__main__":
    # Setup Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin.settings')
    django.setup()
    
    run_security_audit()