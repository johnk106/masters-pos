#!/usr/bin/env python3
"""
Simple Security Audit Script
Scans views for security decorators and generates a report.
"""

import os
import sys
import django
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin.settings')
django.setup()

from django.urls import get_resolver
from django.conf import settings
import importlib
import inspect
import re


def find_view_functions():
    """Find all view functions in the project"""
    views = []
    
    # Get all Python files in the project
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['venv', '__pycache__', '.git', 'migrations']):
            continue
            
        for file in files:
            if file == 'views.py':
                file_path = os.path.join(root, file)
                module_path = file_path.replace('./', '').replace('/', '.').replace('.py', '')
                
                try:
                    # Import the module
                    module = importlib.import_module(module_path)
                    
                    # Find all functions that look like views
                    for name, obj in inspect.getmembers(module):
                        if inspect.isfunction(obj) and hasattr(obj, '__code__'):
                            # Check if it's likely a view function
                            if 'request' in obj.__code__.co_varnames:
                                views.append({
                                    'name': name,
                                    'module': module_path,
                                    'function': obj,
                                    'file_path': file_path
                                })
                except Exception as e:
                    print(f"Warning: Could not import {module_path}: {e}")
    
    return views


def check_view_protection(view_info):
    """Check if a view has security decorators"""
    func = view_info['function']
    file_path = view_info['file_path']
    
    # Read the source file to check for decorators
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except:
        return {'protected': False, 'decorators': [], 'error': 'Could not read file'}
    
    # Find the function definition
    func_pattern = rf'def\s+{re.escape(view_info["name"])}\s*\('
    match = re.search(func_pattern, content)
    
    if not match:
        return {'protected': False, 'decorators': [], 'error': 'Function not found'}
    
    # Look for decorators before the function
    func_start = match.start()
    lines_before = content[:func_start].split('\n')
    
    # Look for decorators in the lines before the function
    decorators = []
    for line in reversed(lines_before[-10:]):  # Check last 10 lines
        line = line.strip()
        if line.startswith('@'):
            decorators.append(line)
        elif line and not line.startswith('#'):
            break
    
    # Check for security-related decorators
    security_decorators = [
        '@login_required',
        '@permission_required',
        '@user_passes_test',
        '@has_role',
        '@has_any_role',
        '@has_permission',
        '@admin_only',
        '@manager_or_above',
        '@admin_or_manager_required'
    ]
    
    protected = any(
        any(sec_dec in decorator for sec_dec in security_decorators)
        for decorator in decorators
    )
    
    return {
        'protected': protected,
        'decorators': decorators,
        'error': None
    }


def main():
    """Main audit function"""
    print("🔍 Starting Security Audit...")
    print("=" * 50)
    
    views = find_view_functions()
    print(f"Found {len(views)} view functions")
    
    protected_views = []
    unprotected_views = []
    
    for view in views:
        protection_info = check_view_protection(view)
        
        if protection_info['error']:
            print(f"❌ Error checking {view['name']}: {protection_info['error']}")
            continue
        
        if protection_info['protected']:
            protected_views.append({
                'view': view,
                'protection': protection_info
            })
        else:
            unprotected_views.append({
                'view': view,
                'protection': protection_info
            })
    
    # Generate report
    print("\n📊 SECURITY AUDIT REPORT")
    print("=" * 50)
    
    print(f"✅ Protected views: {len(protected_views)}")
    print(f"❌ Unprotected views: {len(unprotected_views)}")
    print(f"📈 Protection rate: {len(protected_views) / len(views) * 100:.1f}%")
    
    if unprotected_views:
        print("\n🚨 UNPROTECTED VIEWS:")
        print("-" * 30)
        for item in unprotected_views:
            view = item['view']
            print(f"  • {view['module']}.{view['name']}")
            print(f"    File: {view['file_path']}")
            if item['protection']['decorators']:
                print(f"    Decorators: {', '.join(item['protection']['decorators'])}")
            print()
    
    if protected_views:
        print("\n✅ PROTECTED VIEWS:")
        print("-" * 30)
        for item in protected_views:
            view = item['view']
            print(f"  • {view['module']}.{view['name']}")
            print(f"    Decorators: {', '.join(item['protection']['decorators'])}")
            print()
    
    # Save report to file
    report_path = 'security_audit_report.json'
    import json
    
    report_data = {
        'timestamp': str(django.utils.timezone.now()),
        'total_views': len(views),
        'protected_views': len(protected_views),
        'unprotected_views': len(unprotected_views),
        'protection_rate': len(protected_views) / len(views) * 100 if views else 0,
        'unprotected_view_details': [
            {
                'name': item['view']['name'],
                'module': item['view']['module'],
                'file_path': item['view']['file_path'],
                'decorators': item['protection']['decorators']
            }
            for item in unprotected_views
        ]
    }
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\n📄 Report saved to: {report_path}")
    
    return len(unprotected_views) == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)