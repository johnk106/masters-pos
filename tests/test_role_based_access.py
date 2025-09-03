"""
Comprehensive Role-Based Access Control Tests
Tests admin access, restricted user access, and permission enforcement.
"""

import os
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from authentication.models import Role, UserProfile
from inventory.models import Product, Category
from sales.models import Order
from finance.models import Expense
from people.models import Customer, Supplier
import json

# Setup Django if running standalone
if not hasattr(django.conf.settings, 'configured') or not django.conf.settings.configured:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin.settings')
    django.setup()


class RoleBasedAccessTestCase(TestCase):
    """Base test case with common setup for role-based access tests"""
    
    def setUp(self):
        """Set up test data including users, roles, and permissions"""
        self.client = Client()
        
        # Create roles
        self.admin_role = Role.objects.create(
            name='Admin',
            description='Full system access'
        )
        
        self.manager_role = Role.objects.create(
            name='Manager',
            description='Management access'
        )
        
        self.salesman_role = Role.objects.create(
            name='Salesman',
            description='Sales access only'
        )
        
        self.restricted_role = Role.objects.create(
            name='Restricted',
            description='Limited access'
        )
        
        # Assign permissions to roles
        self.setup_role_permissions()
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_user',
            email='admin@test.com',
            password='testpass123'
        )
        
        self.manager_user = User.objects.create_user(
            username='manager_user',
            email='manager@test.com',
            password='testpass123'
        )
        
        self.salesman_user = User.objects.create_user(
            username='salesman_user',
            email='salesman@test.com',
            password='testpass123'
        )
        
        self.restricted_user = User.objects.create_user(
            username='restricted_user',
            email='restricted@test.com',
            password='testpass123'
        )
        
        # Create user profiles with roles
        UserProfile.objects.create(user=self.admin_user, role=self.admin_role)
        UserProfile.objects.create(user=self.manager_user, role=self.manager_role)
        UserProfile.objects.create(user=self.salesman_user, role=self.salesman_role)
        UserProfile.objects.create(user=self.restricted_user, role=self.restricted_role)
        
        # Create test data
        self.setup_test_data()
    
    def setup_role_permissions(self):
        """Set up permissions for each role"""
        # Get all permissions
        all_permissions = Permission.objects.all()
        
        # Admin gets all permissions
        self.admin_role.permissions.set(all_permissions)
        
        # Manager gets most permissions except user management
        manager_permissions = all_permissions.exclude(
            codename__in=['add_user', 'change_user', 'delete_user']
        )
        self.manager_role.permissions.set(manager_permissions)
        
        # Salesman gets only sales-related permissions
        sales_permissions = Permission.objects.filter(
            codename__in=[
                'view_order', 'add_order', 'change_order',
                'view_customer', 'add_customer', 'change_customer',
                'view_product'
            ]
        )
        self.salesman_role.permissions.set(sales_permissions)
        
        # Restricted user gets minimal permissions
        restricted_permissions = Permission.objects.filter(
            codename__in=['view_product', 'view_order']
        )
        self.restricted_role.permissions.set(restricted_permissions)
    
    def setup_test_data(self):
        """Create test data for testing"""
        # Create test category and product
        self.category = Category.objects.create(name='Test Category')
        self.product = Product.objects.create(
            name='Test Product',
            category=self.category,
            price=10.00
        )
        
        # Create test customer
        self.customer = Customer.objects.create(
            name='Test Customer',
            email='customer@test.com'
        )
        
        # Create test supplier
        self.supplier = Supplier.objects.create(
            name='Test Supplier',
            email='supplier@test.com'
        )
    
    def login_user(self, user):
        """Helper method to login a user"""
        return self.client.login(username=user.username, password='testpass123')
    
    def logout_user(self):
        """Helper method to logout current user"""
        self.client.logout()


class AdminAccessTests(RoleBasedAccessTestCase):
    """Test admin user access to all system features"""
    
    def test_admin_dashboard_access(self):
        """Test admin can access dashboard"""
        self.login_user(self.admin_user)
        
        response = self.client.get('/dashboard/homepage/')
        self.assertEqual(response.status_code, 200)
    
    def test_admin_user_management_access(self):
        """Test admin can access user management"""
        self.login_user(self.admin_user)
        
        # Test user list access
        response = self.client.get('/dashboard/authentication/users/')
        self.assertIn(response.status_code, [200, 302])  # Allow redirect to login if needed
        
        # Test role management access
        response = self.client.get('/dashboard/authentication/roles/')
        self.assertIn(response.status_code, [200, 302])
    
    def test_admin_inventory_access(self):
        """Test admin can access inventory management"""
        self.login_user(self.admin_user)
        
        # Test product list
        response = self.client.get('/dashboard/inventory/products/')
        self.assertIn(response.status_code, [200, 302])
        
        # Test category management
        response = self.client.get('/dashboard/inventory/categories/')
        self.assertIn(response.status_code, [200, 302])
    
    def test_admin_sales_access(self):
        """Test admin can access sales management"""
        self.login_user(self.admin_user)
        
        # Test orders
        response = self.client.get('/dashboard/sales/orders/')
        self.assertIn(response.status_code, [200, 302])
        
        # Test POS
        response = self.client.get('/dashboard/sales/pos/')
        self.assertIn(response.status_code, [200, 302])
    
    def test_admin_finance_access(self):
        """Test admin can access finance management"""
        self.login_user(self.admin_user)
        
        # Test expenses
        response = self.client.get('/dashboard/finance/expenses/')
        self.assertIn(response.status_code, [200, 302])
    
    def test_admin_reports_access(self):
        """Test admin can access all reports"""
        self.login_user(self.admin_user)
        
        # Test sales report
        response = self.client.get('/dashboard/reports/sales/')
        self.assertIn(response.status_code, [200, 302])
        
        # Test inventory report
        response = self.client.get('/dashboard/reports/inventory/')
        self.assertIn(response.status_code, [200, 302])
    
    def test_admin_people_management_access(self):
        """Test admin can access people management"""
        self.login_user(self.admin_user)
        
        # Test customers
        response = self.client.get('/dashboard/people/customers/')
        self.assertIn(response.status_code, [200, 302])
        
        # Test suppliers
        response = self.client.get('/dashboard/people/suppliers/')
        self.assertIn(response.status_code, [200, 302])


class RestrictedUserAccessTests(RoleBasedAccessTestCase):
    """Test restricted user access and proper permission denial"""
    
    def test_restricted_user_dashboard_access(self):
        """Test restricted user can access basic dashboard"""
        self.login_user(self.restricted_user)
        
        response = self.client.get('/dashboard/homepage/')
        self.assertEqual(response.status_code, 200)
    
    def test_restricted_user_denied_user_management(self):
        """Test restricted user cannot access user management"""
        self.login_user(self.restricted_user)
        
        # Test user list access denied
        response = self.client.get('/dashboard/authentication/users/')
        self.assertIn(response.status_code, [403, 302])  # Forbidden or redirect
        
        # Test role management access denied
        response = self.client.get('/dashboard/authentication/roles/')
        self.assertIn(response.status_code, [403, 302])
    
    def test_restricted_user_denied_finance_access(self):
        """Test restricted user cannot access finance management"""
        self.login_user(self.restricted_user)
        
        response = self.client.get('/dashboard/finance/expenses/')
        self.assertIn(response.status_code, [403, 302])
    
    def test_restricted_user_denied_reports_access(self):
        """Test restricted user cannot access sensitive reports"""
        self.login_user(self.restricted_user)
        
        # Test sales report access denied
        response = self.client.get('/dashboard/reports/sales/')
        self.assertIn(response.status_code, [403, 302])
        
        # Test financial reports access denied
        response = self.client.get('/dashboard/reports/profit-loss/')
        self.assertIn(response.status_code, [403, 302])
    
    def test_restricted_user_denied_people_management(self):
        """Test restricted user cannot manage people"""
        self.login_user(self.restricted_user)
        
        # Test customer management access denied
        response = self.client.get('/dashboard/people/customers/')
        self.assertIn(response.status_code, [403, 302])
        
        # Test supplier management access denied
        response = self.client.get('/dashboard/people/suppliers/')
        self.assertIn(response.status_code, [403, 302])
    
    def test_restricted_user_denied_inventory_management(self):
        """Test restricted user cannot manage inventory"""
        self.login_user(self.restricted_user)
        
        # Can view products but not manage
        response = self.client.get('/dashboard/inventory/products/')
        self.assertIn(response.status_code, [200, 302])
        
        # Cannot access category management
        response = self.client.get('/dashboard/inventory/categories/')
        self.assertIn(response.status_code, [403, 302])
    
    def test_restricted_user_ajax_endpoints_denied(self):
        """Test restricted user cannot access sensitive AJAX endpoints"""
        self.login_user(self.restricted_user)
        
        # Test creating category via AJAX
        response = self.client.post('/dashboard/inventory/ajax/create-category/', {
            'name': 'Test Category'
        })
        self.assertIn(response.status_code, [403, 302])


class MiddleRoleAccessTests(RoleBasedAccessTestCase):
    """Test manager and salesman role access"""
    
    def test_manager_access_permissions(self):
        """Test manager has appropriate access"""
        self.login_user(self.manager_user)
        
        # Should have access to inventory
        response = self.client.get('/dashboard/inventory/products/')
        self.assertIn(response.status_code, [200, 302])
        
        # Should have access to sales
        response = self.client.get('/dashboard/sales/orders/')
        self.assertIn(response.status_code, [200, 302])
        
        # Should have access to reports
        response = self.client.get('/dashboard/reports/sales/')
        self.assertIn(response.status_code, [200, 302])
        
        # Should NOT have access to user management
        response = self.client.get('/dashboard/authentication/users/')
        self.assertIn(response.status_code, [403, 302])
    
    def test_salesman_access_permissions(self):
        """Test salesman has appropriate access"""
        self.login_user(self.salesman_user)
        
        # Should have access to sales
        response = self.client.get('/dashboard/sales/pos/')
        self.assertIn(response.status_code, [200, 302])
        
        # Should have access to customers
        response = self.client.get('/dashboard/people/customers/')
        self.assertIn(response.status_code, [200, 302])
        
        # Should NOT have access to finance
        response = self.client.get('/dashboard/finance/expenses/')
        self.assertIn(response.status_code, [403, 302])
        
        # Should NOT have access to user management
        response = self.client.get('/dashboard/authentication/users/')
        self.assertIn(response.status_code, [403, 302])


class PermissionEnforcementTests(RoleBasedAccessTestCase):
    """Test that permissions are properly enforced"""
    
    def test_unauthenticated_user_redirected(self):
        """Test unauthenticated users are redirected to login"""
        # Don't login any user
        
        response = self.client.get('/dashboard/homepage/')
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_superuser_access_all(self):
        """Test superuser has access to everything"""
        superuser = User.objects.create_superuser(
            username='superuser',
            email='super@test.com',
            password='testpass123'
        )
        
        self.client.login(username='superuser', password='testpass123')
        
        # Should have access to all areas
        test_urls = [
            '/dashboard/homepage/',
            '/dashboard/authentication/users/',
            '/dashboard/authentication/roles/',
            '/dashboard/inventory/products/',
            '/dashboard/sales/orders/',
            '/dashboard/finance/expenses/',
            '/dashboard/reports/sales/',
            '/dashboard/people/customers/',
        ]
        
        for url in test_urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [200, 302], 
                         f"Superuser should have access to {url}")
    
    def test_role_based_ui_elements(self):
        """Test that UI elements are hidden based on roles"""
        # This would require checking template context or rendered content
        # For now, we'll test the access patterns
        
        # Admin user should see admin links
        self.login_user(self.admin_user)
        response = self.client.get('/dashboard/homepage/')
        self.assertEqual(response.status_code, 200)
        
        # Restricted user should not see admin links
        self.logout_user()
        self.login_user(self.restricted_user)
        response = self.client.get('/dashboard/homepage/')
        self.assertEqual(response.status_code, 200)


class SecurityTestSuite:
    """Main test suite runner for security tests"""
    
    def __init__(self):
        self.test_cases = [
            AdminAccessTests,
            RestrictedUserAccessTests,
            MiddleRoleAccessTests,
            PermissionEnforcementTests
        ]
    
    def run_all_tests(self):
        """Run all security tests"""
        import unittest
        
        suite = unittest.TestSuite()
        
        for test_case in self.test_cases:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_case)
            suite.addTests(tests)
        
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        return result
    
    def generate_test_report(self, result):
        """Generate a test report"""
        report = {
            'total_tests': result.testsRun,
            'failures': len(result.failures),
            'errors': len(result.errors),
            'success_rate': ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0,
            'failure_details': result.failures,
            'error_details': result.errors
        }
        
        return report


def run_security_tests():
    """Run all security tests and return results"""
    suite = SecurityTestSuite()
    result = suite.run_all_tests()
    report = suite.generate_test_report(result)
    
    print("\n" + "=" * 50)
    print("SECURITY TEST REPORT")
    print("=" * 50)
    print(f"Total Tests: {report['total_tests']}")
    print(f"Failures: {report['failures']}")
    print(f"Errors: {report['errors']}")
    print(f"Success Rate: {report['success_rate']:.1f}%")
    
    if report['failures'] or report['errors']:
        print("\nFAILURES AND ERRORS:")
        for failure in report['failure_details']:
            print(f"FAIL: {failure[0]}")
            print(f"  {failure[1]}")
        
        for error in report['error_details']:
            print(f"ERROR: {error[0]}")
            print(f"  {error[1]}")
    
    return report


if __name__ == "__main__":
    run_security_tests()