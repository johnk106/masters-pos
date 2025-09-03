"""
Comprehensive Security Tests for Role-Based Access Control
Tests admin access, restricted user access, and permission enforcement.
"""

import os
import django
from django.test import TestCase, Client
from django.contrib.auth.models import User, Permission, Group
from django.urls import reverse
from django.contrib.contenttypes.models import ContentType
from authentication.models import Role, UserProfile
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin.settings')
django.setup()


class SecurityTestCase(TestCase):
    """Base test case for security tests"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create roles
        self.admin_role, _ = Role.objects.get_or_create(
            name='Admin',
            defaults={'description': 'Full system access'}
        )
        
        self.manager_role, _ = Role.objects.get_or_create(
            name='Manager',
            defaults={'description': 'Manager access'}
        )
        
        self.staff_role, _ = Role.objects.get_or_create(
            name='Staff',
            defaults={'description': 'Limited staff access'}
        )
        
        # Create test users
        self.admin_user = User.objects.create_user(
            username='admin_test',
            email='admin@test.com',
            password='test123456'
        )
        
        self.manager_user = User.objects.create_user(
            username='manager_test',
            email='manager@test.com',
            password='test123456'
        )
        
        self.staff_user = User.objects.create_user(
            username='staff_test',
            email='staff@test.com',
            password='test123456'
        )
        
        self.restricted_user = User.objects.create_user(
            username='restricted_test',
            email='restricted@test.com',
            password='test123456'
        )
        
        # Create user profiles with roles
        UserProfile.objects.create(user=self.admin_user, role=self.admin_role)
        UserProfile.objects.create(user=self.manager_user, role=self.manager_role)
        UserProfile.objects.create(user=self.staff_user, role=self.staff_role)
        UserProfile.objects.create(user=self.restricted_user, role=self.staff_role)
        
        # Set up permissions
        self.admin_user.is_staff = True
        self.admin_user.is_superuser = True
        self.admin_user.save()
        
        self.manager_user.is_staff = True
        self.manager_user.save()


class AdminAccessTests(SecurityTestCase):
    """Test admin user access to protected resources"""
    
    def test_admin_dashboard_access(self):
        """Test admin can access dashboard"""
        self.client.login(username='admin_test', password='test123456')
        
        # Test main dashboard
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Test sales dashboard
        response = self.client.get('/sales-dashboard/')
        self.assertEqual(response.status_code, 200)
    
    def test_admin_inventory_access(self):
        """Test admin can access inventory management"""
        self.client.login(username='admin_test', password='test123456')
        
        inventory_urls = [
            '/inventory/products/',
            '/inventory/categories/',
            '/inventory/units/',
            '/inventory/variants/',
            '/inventory/low-stocks/',
        ]
        
        for url in inventory_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, [200, 302])  # 302 for redirects
    
    def test_admin_sales_access(self):
        """Test admin can access sales management"""
        self.client.login(username='admin_test', password='test123456')
        
        sales_urls = [
            '/sales/pos/',
            '/sales/orders/',
            '/sales/online-orders/',
            '/sales/returns/',
        ]
        
        for url in sales_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, [200, 302])
    
    def test_admin_reports_access(self):
        """Test admin can access reports"""
        self.client.login(username='admin_test', password='test123456')
        
        report_urls = [
            '/reports/sales/',
            '/reports/inventory/',
            '/reports/profit-loss/',
            '/reports/expense/',
            '/reports/purchase/',
        ]
        
        for url in report_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, [200, 302])
    
    def test_admin_user_management_access(self):
        """Test admin can access user management"""
        self.client.login(username='admin_test', password='test123456')
        
        user_mgmt_urls = [
            '/auth/users/',
            '/auth/roles/',
            '/auth/permissions/',
        ]
        
        for url in user_mgmt_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, [200, 302])


class RestrictedUserAccessTests(SecurityTestCase):
    """Test restricted user access and proper blocking"""
    
    def test_restricted_user_blocked_from_admin_pages(self):
        """Test restricted user cannot access admin-only pages"""
        self.client.login(username='restricted_test', password='test123456')
        
        admin_only_urls = [
            '/auth/users/',
            '/auth/roles/',
            '/auth/permissions/',
            '/auth/users/create/',
            '/auth/roles/create/',
        ]
        
        for url in admin_only_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                # Should get 403 Forbidden or redirect to login/access denied
                self.assertIn(response.status_code, [403, 302])
                
                if response.status_code == 302:
                    # Check if redirected to login or access denied
                    self.assertTrue(
                        'login' in response.url.lower() or 
                        'access-denied' in response.url.lower() or
                        'forbidden' in response.url.lower()
                    )
    
    def test_restricted_user_cannot_access_sensitive_reports(self):
        """Test restricted user cannot access sensitive reports"""
        self.client.login(username='restricted_test', password='test123456')
        
        sensitive_report_urls = [
            '/reports/profit-loss/',
            '/reports/expense/',
            '/reports/financial-summary/',
        ]
        
        for url in sensitive_report_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, [403, 302])
    
    def test_restricted_user_cannot_modify_inventory(self):
        """Test restricted user cannot modify inventory"""
        self.client.login(username='restricted_test', password='test123456')
        
        modification_urls = [
            '/inventory/products/create/',
            '/inventory/categories/create/',
            '/inventory/units/create/',
        ]
        
        for url in modification_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, [403, 302])


class ManagerAccessTests(SecurityTestCase):
    """Test manager user access levels"""
    
    def test_manager_can_access_management_features(self):
        """Test manager can access appropriate management features"""
        self.client.login(username='manager_test', password='test123456')
        
        manager_urls = [
            '/inventory/products/',
            '/sales/pos/',
            '/reports/sales/',
            '/reports/inventory/',
        ]
        
        for url in manager_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, [200, 302])
    
    def test_manager_blocked_from_admin_only_features(self):
        """Test manager cannot access admin-only features"""
        self.client.login(username='manager_test', password='test123456')
        
        admin_only_urls = [
            '/auth/roles/',
            '/auth/permissions/',
            '/auth/roles/create/',
        ]
        
        for url in admin_only_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, [403, 302])


class SecurityMiddlewareTests(SecurityTestCase):
    """Test security middleware functionality"""
    
    def test_unauthenticated_user_redirected(self):
        """Test unauthenticated users are redirected to login"""
        protected_urls = [
            '/inventory/products/',
            '/sales/pos/',
            '/reports/sales/',
            '/auth/users/',
        ]
        
        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, [302, 403])
                
                if response.status_code == 302:
                    self.assertTrue('login' in response.url.lower())
    
    def test_csrf_protection(self):
        """Test CSRF protection is working"""
        self.client.login(username='admin_test', password='test123456')
        
        # Try to make POST request without CSRF token
        response = self.client.post('/inventory/products/create/', {
            'name': 'Test Product',
            'price': '10.00'
        })
        
        # Should fail due to missing CSRF token
        self.assertIn(response.status_code, [403, 400])


class APISecurityTests(SecurityTestCase):
    """Test API endpoint security"""
    
    def test_ajax_endpoints_require_authentication(self):
        """Test AJAX endpoints require authentication"""
        ajax_urls = [
            '/sales/cash-register-data/',
            '/sales/today-profit-data/',
            '/inventory/ajax/get-subcategories/',
            '/purchases/ajax/get-products/',
        ]
        
        for url in ajax_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, [302, 403, 401])
    
    def test_ajax_endpoints_with_authentication(self):
        """Test AJAX endpoints work with proper authentication"""
        self.client.login(username='admin_test', password='test123456')
        
        ajax_urls = [
            '/sales/cash-register-data/',
            '/sales/today-profit-data/',
        ]
        
        for url in ajax_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertIn(response.status_code, [200, 302])


def run_all_security_tests():
    """Run all security tests and return results"""
    import unittest
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(AdminAccessTests))
    suite.addTests(loader.loadTestsFromTestCase(RestrictedUserAccessTests))
    suite.addTests(loader.loadTestsFromTestCase(ManagerAccessTests))
    suite.addTests(loader.loadTestsFromTestCase(SecurityMiddlewareTests))
    suite.addTests(loader.loadTestsFromTestCase(APISecurityTests))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return {
        'tests_run': result.testsRun,
        'failures': len(result.failures),
        'errors': len(result.errors),
        'success': result.wasSuccessful()
    }


if __name__ == '__main__':
    results = run_all_security_tests()
    print(f"\n🔍 Security Test Results:")
    print(f"Tests run: {results['tests_run']}")
    print(f"Failures: {results['failures']}")
    print(f"Errors: {results['errors']}")
    print(f"Success: {results['success']}")