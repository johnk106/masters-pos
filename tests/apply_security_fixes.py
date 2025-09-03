#!/usr/bin/env python3
"""
Security Fixer Script
Automatically applies security decorators to unprotected views based on their context.
"""

import os
import re
import json
from pathlib import Path


class SecurityFixer:
    """Automatically apply security decorators to unprotected views"""
    
    def __init__(self):
        self.fixes_applied = []
        self.backup_files = []
        
        # Define security rules based on view patterns
        self.security_rules = {
            # Admin-only views
            'admin_only': [
                r'.*user.*manage.*',
                r'.*role.*manage.*',
                r'.*permission.*',
                r'.*create_user.*',
                r'.*delete_user.*',
                r'.*create_role.*',
                r'.*delete_role.*',
                r'.*manage_permissions.*',
            ],
            
            # Manager or above views
            'manager_or_above': [
                r'.*report.*profit.*',
                r'.*report.*expense.*',
                r'.*financial.*',
                r'.*expense.*',
                r'.*purchase.*',
                r'.*supplier.*',
            ],
            
            # Staff level views (login required)
            'login_required': [
                r'.*dashboard.*',
                r'.*inventory.*',
                r'.*product.*',
                r'.*category.*',
                r'.*customer.*',
                r'.*sales.*',
                r'.*pos.*',
                r'.*order.*',
                r'.*profile.*',
                r'.*settings.*',
            ],
            
            # Public views (no protection needed)
            'public': [
                r'.*login.*',
                r'.*logout.*',
                r'.*homepage.*',
                r'.*faqs.*',
            ]
        }
    
    def determine_security_level(self, view_name, module_name):
        """Determine the appropriate security level for a view"""
        full_name = f"{module_name}.{view_name}".lower()
        
        # Check if it's a public view
        for pattern in self.security_rules['public']:
            if re.search(pattern, full_name):
                return 'public'
        
        # Check if it's admin-only
        for pattern in self.security_rules['admin_only']:
            if re.search(pattern, full_name):
                return 'admin_only'
        
        # Check if it's manager or above
        for pattern in self.security_rules['manager_or_above']:
            if re.search(pattern, full_name):
                return 'manager_or_above'
        
        # Default to login required
        return 'login_required'
    
    def get_decorator_for_level(self, security_level):
        """Get the appropriate decorator for a security level"""
        decorators = {
            'admin_only': '@admin_only',
            'manager_or_above': '@manager_or_above',
            'login_required': '@login_required',
            'public': None
        }
        return decorators.get(security_level)
    
    def get_import_for_decorator(self, decorator):
        """Get the import statement needed for a decorator"""
        imports = {
            '@admin_only': 'from authentication.decorators import admin_only',
            '@manager_or_above': 'from authentication.decorators import manager_or_above',
            '@login_required': 'from django.contrib.auth.decorators import login_required',
        }
        return imports.get(decorator)
    
    def create_backup(self, file_path):
        """Create a backup of the original file"""
        backup_path = f"{file_path}.security_backup"
        
        try:
            with open(file_path, 'r') as original:
                content = original.read()
            
            with open(backup_path, 'w') as backup:
                backup.write(content)
            
            self.backup_files.append(backup_path)
            print(f"✅ Created backup: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to create backup for {file_path}: {e}")
            return False
    
    def add_decorator_to_view(self, file_path, view_name, decorator):
        """Add a security decorator to a specific view"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Find the view function
            view_pattern = rf'^def\s+{re.escape(view_name)}\s*\('
            view_line_idx = None
            
            for i, line in enumerate(lines):
                if re.search(view_pattern, line):
                    view_line_idx = i
                    break
            
            if view_line_idx is None:
                print(f"❌ Could not find view {view_name} in {file_path}")
                return False
            
            # Find the right place to insert the decorator
            # Look for existing decorators or the function definition
            insert_idx = view_line_idx
            
            # Check if there are already decorators
            for i in range(view_line_idx - 1, -1, -1):
                line = lines[i].strip()
                if line.startswith('@'):
                    continue
                elif line == '' or line.startswith('#'):
                    continue
                else:
                    insert_idx = i + 1
                    break
            
            # Get the indentation of the function
            func_line = lines[view_line_idx]
            indent = len(func_line) - len(func_line.lstrip())
            
            # Insert the decorator
            decorator_line = ' ' * indent + decorator + '\n'
            lines.insert(insert_idx, decorator_line)
            
            # Write back to file
            with open(file_path, 'w') as f:
                f.writelines(lines)
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to add decorator to {view_name} in {file_path}: {e}")
            return False
    
    def add_import_to_file(self, file_path, import_statement):
        """Add an import statement to a file if it doesn't exist"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if import already exists
            if import_statement in content:
                return True
            
            lines = content.split('\n')
            
            # Find the right place to insert the import
            # Look for existing imports
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('from ') or line.strip().startswith('import '):
                    insert_idx = i + 1
                elif line.strip() == '':
                    continue
                else:
                    break
            
            # Insert the import
            lines.insert(insert_idx, import_statement)
            
            # Write back to file
            with open(file_path, 'w') as f:
                f.write('\n'.join(lines))
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to add import to {file_path}: {e}")
            return False
    
    def apply_fixes(self):
        """Apply security fixes to all unprotected views"""
        # Load the security audit report
        try:
            with open('security_audit_report.json', 'r') as f:
                audit_data = json.load(f)
        except FileNotFoundError:
            print("❌ Security audit report not found. Run the audit first.")
            return False
        
        unprotected_views = audit_data.get('unprotected_view_details', [])
        
        if not unprotected_views:
            print("✅ No unprotected views found!")
            return True
        
        print(f"🔧 Applying security fixes to {len(unprotected_views)} unprotected views...")
        
        # Group views by file for efficient processing
        files_to_fix = {}
        for view in unprotected_views:
            file_path = view['file_path']
            if file_path not in files_to_fix:
                files_to_fix[file_path] = []
            files_to_fix[file_path].append(view)
        
        # Process each file
        for file_path, views in files_to_fix.items():
            print(f"\n📄 Processing {file_path}...")
            
            # Create backup
            if not self.create_backup(file_path):
                continue
            
            # Track imports needed
            imports_needed = set()
            
            # Apply fixes to each view in the file
            for view in views:
                view_name = view['name']
                module_name = view['module']
                
                # Determine security level
                security_level = self.determine_security_level(view_name, module_name)
                decorator = self.get_decorator_for_level(security_level)
                
                if decorator is None:
                    print(f"  ℹ️  {view_name} is public - no protection needed")
                    continue
                
                # Add decorator to view
                if self.add_decorator_to_view(file_path, view_name, decorator):
                    print(f"  ✅ Added {decorator} to {view_name}")
                    imports_needed.add(decorator)
                    self.fixes_applied.append({
                        'file': file_path,
                        'view': view_name,
                        'decorator': decorator,
                        'security_level': security_level
                    })
                else:
                    print(f"  ❌ Failed to add {decorator} to {view_name}")
            
            # Add necessary imports
            for decorator in imports_needed:
                import_statement = self.get_import_for_decorator(decorator)
                if import_statement:
                    if self.add_import_to_file(file_path, import_statement):
                        print(f"  ✅ Added import: {import_statement}")
                    else:
                        print(f"  ❌ Failed to add import: {import_statement}")
        
        return True
    
    def generate_report(self):
        """Generate a report of all applied fixes"""
        report = {
            'timestamp': str(os.popen('date').read().strip()),
            'fixes_applied': len(self.fixes_applied),
            'backup_files': self.backup_files,
            'details': self.fixes_applied
        }
        
        with open('security_fixes_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 SECURITY FIXES REPORT")
        print("=" * 50)
        print(f"✅ Fixes applied: {len(self.fixes_applied)}")
        print(f"📄 Backup files created: {len(self.backup_files)}")
        print(f"📄 Report saved to: security_fixes_report.json")
        
        if self.fixes_applied:
            print("\n🔧 APPLIED FIXES:")
            print("-" * 30)
            for fix in self.fixes_applied:
                print(f"  • {fix['view']} ({fix['security_level']})")
                print(f"    File: {fix['file']}")
                print(f"    Decorator: {fix['decorator']}")
                print()
    
    def restore_backups(self):
        """Restore all backup files"""
        restored = 0
        for backup_path in self.backup_files:
            original_path = backup_path.replace('.security_backup', '')
            try:
                with open(backup_path, 'r') as backup:
                    content = backup.read()
                
                with open(original_path, 'w') as original:
                    original.write(content)
                
                os.remove(backup_path)
                restored += 1
                print(f"✅ Restored: {original_path}")
            except Exception as e:
                print(f"❌ Failed to restore {original_path}: {e}")
        
        print(f"\n📊 Restored {restored} files from backups")


def main():
    """Main function"""
    import sys
    
    fixer = SecurityFixer()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--restore':
        print("🔄 Restoring backups...")
        fixer.restore_backups()
        return
    
    print("🔧 Starting Security Fixes Application...")
    print("=" * 50)
    
    if fixer.apply_fixes():
        fixer.generate_report()
        print("\n✅ Security fixes applied successfully!")
        print("💡 To restore backups, run: python3 apply_security_fixes.py --restore")
    else:
        print("\n❌ Failed to apply security fixes")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())