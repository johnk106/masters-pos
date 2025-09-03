"""
Security Fixer Script
Automatically applies missing security decorators to unprotected views.
"""

import os
import re
import ast
import django
from django.conf import settings
from .security_audit import SecurityAudit

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin.settings')
django.setup()


class SecurityFixer:
    """Automatically apply security decorators to unprotected views"""
    
    def __init__(self):
        self.auditor = SecurityAudit()
        self.fixes_applied = []
        self.backup_files = []
    
    def create_backup(self, file_path):
        """Create a backup of the original file"""
        backup_path = f"{file_path}.security_backup"
        
        try:
            with open(file_path, 'r') as original:
                content = original.read()
            
            with open(backup_path, 'w') as backup:
                backup.write(content)
            
            self.backup_files.append(backup_path)
            return True
        except Exception as e:
            print(f"Error creating backup for {file_path}: {e}")
            return False
    
    def get_view_decorator_mapping(self):
        """Define which decorators to apply to which types of views"""
        return {
            # Authentication views
            'authentication': {
                'users': '@admin_only',
                'roles': '@admin_only',
                'create_user': '@admin_only',
                'edit_user': '@admin_only',
                'delete_user': '@admin_only',
                'create_role': '@admin_only',
                'edit_role': '@admin_only',
                'delete_role': '@admin_only',
                'manage_permissions': '@admin_only',
                'default': '@admin_or_manager_required'
            },
            
            # Inventory views
            'inventory': {
                'create_product': '@manager_or_above',
                'edit_product': '@manager_or_above',
                'delete_product': '@manager_or_above',
                'create_category': '@manager_or_above',
                'edit_category': '@manager_or_above',
                'delete_category': '@manager_or_above',
                'default': '@has_any_role(["Admin", "Manager", "Inventory Manager", "Store Keeper"])'
            },
            
            # Sales views
            'sales': {
                'delete_order': '@manager_or_above',
                'update_payment': '@manager_or_above',
                'default': '@has_any_role(["Admin", "Manager", "Salesman"])'
            },
            
            # Finance views
            'finance': {
                'default': '@admin_or_manager_required'
            },
            
            # Reports views
            'reports': {
                'default': '@admin_or_manager_required'
            },
            
            # People views
            'people': {
                'delete_customer': '@manager_or_above',
                'delete_supplier': '@manager_or_above',
                'default': '@admin_or_manager_required'
            },
            
            # Purchases views
            'purchases': {
                'default': '@admin_or_manager_required'
            },
            
            # Settings views
            'settings': {
                'default': '@admin_or_manager_required'
            }
        }
    
    def determine_decorator(self, view_info):
        """Determine the appropriate decorator for a view"""
        namespace = view_info['namespace'].lower()
        view_name = view_info['view_name'].lower()
        
        decorator_mapping = self.get_view_decorator_mapping()
        
        # Find the app mapping
        app_mapping = None
        for app_name in decorator_mapping:
            if app_name in namespace:
                app_mapping = decorator_mapping[app_name]
                break
        
        if not app_mapping:
            # Default fallback
            if any(keyword in view_name for keyword in ['delete', 'create', 'edit', 'update']):
                return '@manager_or_above'
            else:
                return '@admin_or_manager_required'
        
        # Check for specific view name matches
        for view_pattern, decorator in app_mapping.items():
            if view_pattern != 'default' and view_pattern in view_name:
                return decorator
        
        # Return default for the app
        return app_mapping.get('default', '@admin_or_manager_required')
    
    def add_import_if_needed(self, file_content, decorator):
        """Add import statement for the decorator if not already present"""
        # Check if authentication decorators import exists
        import_pattern = r'from\s+authentication\.decorators\s+import\s+.*'
        
        if not re.search(import_pattern, file_content):
            # Add the import after other imports
            import_line = "from authentication.decorators import admin_only, admin_or_manager_required, manager_or_above, has_any_role, has_role, has_permission\n"
            
            # Find the last import line
            lines = file_content.split('\n')
            last_import_index = -1
            
            for i, line in enumerate(lines):
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    last_import_index = i
            
            if last_import_index >= 0:
                lines.insert(last_import_index + 1, import_line)
                return '\n'.join(lines)
            else:
                # Add at the beginning
                return import_line + '\n' + file_content
        
        return file_content
    
    def add_decorator_to_function(self, file_content, function_name, decorator):
        """Add decorator to a specific function"""
        # Pattern to find the function definition
        function_pattern = rf'(def\s+{re.escape(function_name)}\s*\([^)]*\):)'
        
        # Check if decorator already exists
        decorator_name = decorator.replace('@', '')
        if decorator_name in file_content:
            return file_content  # Already has some decorator
        
        # Find the function and add decorator
        def add_decorator(match):
            function_def = match.group(1)
            # Add the decorator on the line before the function
            return f"{decorator}\n{function_def}"
        
        modified_content = re.sub(function_pattern, add_decorator, file_content)
        
        return modified_content
    
    def apply_fixes_to_file(self, file_path, view_fixes):
        """Apply security fixes to a specific file"""
        try:
            # Create backup
            if not self.create_backup(file_path):
                return False
            
            # Read file content
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Add imports
            content = self.add_import_if_needed(content, '@admin_only')
            
            # Apply decorators to functions
            for fix in view_fixes:
                view_name = fix['view']['view_name']
                decorator = fix['recommended_decorator']
                
                content = self.add_decorator_to_function(content, view_name, decorator)
                
                self.fixes_applied.append({
                    'file': file_path,
                    'view': view_name,
                    'decorator': decorator
                })
            
            # Write modified content
            with open(file_path, 'w') as f:
                f.write(content)
            
            return True
            
        except Exception as e:
            print(f"Error applying fixes to {file_path}: {e}")
            return False
    
    def apply_security_fixes(self):
        """Apply security fixes to all unprotected views"""
        print("Starting Security Fix Application...")
        print("=" * 50)
        
        # Run audit to get unprotected views
        report = self.auditor.audit_views()
        fixes = self.auditor.get_recommended_fixes()
        
        if not fixes:
            print("No security fixes needed!")
            return
        
        # Group fixes by file
        fixes_by_file = {}
        for fix in fixes:
            file_path = fix['file_path']
            if file_path not in fixes_by_file:
                fixes_by_file[file_path] = []
            fixes_by_file[file_path].append(fix)
        
        # Apply fixes to each file
        for file_path, file_fixes in fixes_by_file.items():
            if file_path == "Unknown":
                continue
            
            print(f"\nApplying fixes to: {file_path}")
            
            # Update decorator recommendations
            for fix in file_fixes:
                fix['recommended_decorator'] = self.determine_decorator(fix['view'])
            
            success = self.apply_fixes_to_file(file_path, file_fixes)
            
            if success:
                print(f"✅ Applied {len(file_fixes)} fixes to {file_path}")
            else:
                print(f"❌ Failed to apply fixes to {file_path}")
        
        self.print_fix_summary()
    
    def print_fix_summary(self):
        """Print a summary of applied fixes"""
        print("\n" + "=" * 50)
        print("SECURITY FIX SUMMARY")
        print("=" * 50)
        
        print(f"Total fixes applied: {len(self.fixes_applied)}")
        print(f"Files modified: {len(set(fix['file'] for fix in self.fixes_applied))}")
        print(f"Backup files created: {len(self.backup_files)}")
        
        if self.fixes_applied:
            print("\nFixes applied:")
            for fix in self.fixes_applied:
                print(f"  {fix['decorator']} → {fix['view']} in {fix['file']}")
        
        if self.backup_files:
            print("\nBackup files created:")
            for backup in self.backup_files:
                print(f"  {backup}")
    
    def rollback_changes(self):
        """Rollback all changes using backup files"""
        print("Rolling back security changes...")
        
        for backup_path in self.backup_files:
            original_path = backup_path.replace('.security_backup', '')
            
            try:
                with open(backup_path, 'r') as backup:
                    content = backup.read()
                
                with open(original_path, 'w') as original:
                    original.write(content)
                
                print(f"✅ Rolled back {original_path}")
                
            except Exception as e:
                print(f"❌ Failed to rollback {original_path}: {e}")
    
    def cleanup_backups(self):
        """Remove backup files"""
        for backup_path in self.backup_files:
            try:
                os.remove(backup_path)
                print(f"Removed backup: {backup_path}")
            except Exception as e:
                print(f"Failed to remove backup {backup_path}: {e}")


def apply_security_fixes():
    """Main function to apply security fixes"""
    fixer = SecurityFixer()
    fixer.apply_security_fixes()
    
    return fixer


def rollback_security_fixes():
    """Rollback security fixes"""
    fixer = SecurityFixer()
    fixer.rollback_changes()
    
    return fixer


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback_security_fixes()
    else:
        apply_security_fixes()