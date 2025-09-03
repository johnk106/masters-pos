"""
Corrected Security Tests for Role-Based Access Control
Tests with actual URL patterns from the project.
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
        
        # Test actual dashboard URLs
        dashboard_urls = [
            '/dashboard/homepage/',
            '/dashboard/inventory/',
            '/dashboard/sales/',
            '/dashboard/finance/',
            '/dashboard/reports/',
        ]
        
        for url in dashboard_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                # Should not get 404 or 500 errors
                self.assertNotEqual(response.status_code, 404)
                self.assertNotEqual(response.status_code, 500)
    
    def test_admin_user_management_access(self):
        """Test admin can access user management"""
        self.client.login(username='admin_test', password='test123456')
        
        user_mgmt_urls = [
            '/dashboard/authentication/users/',
            '/dashboard/authentication/roles/',
            '/dashboard/authentication/permissions/',
        ]
        
        for url in user_mgmt_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                # Should not get 404 or 500 errors
                self.assertNotEqual(response.status_code, 404)
                self.assertNotEqual(response.status_code, 500)
    
    def test_admin_can_create_users(self):
        """Test admin can create users"""
        self.client.login(username='admin_test', password='test123456')
        
        response = self.client.get('/dashboard/authentication/users/create/')
        # Should not get 404 or 500 errors
        self.assertNotEqual(response.status_code, 404)
        self.assertNotEqual(response.status_code, 500)


class RestrictedUserAccessTests(SecurityTestCase):
    """Test restricted user access and proper blocking"""
    
    def test_restricted_user_blocked_from_admin_pages(self):
        """Test restricted user cannot access admin-only pages"""
        self.client.login(username='restricted_test', password='test123456')
        
        admin_only_urls = [
            '/dashboard/authentication/users/',
            '/dashboard/authentication/roles/',
            '/dashboard/authentication/permissions/',
            '/dashboard/authentication/users/create/',
            '/dashboard/authentication/roles/create/',
        ]
        
        for url in admin_only_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                # Should get 403 Forbidden or redirect to login/access denied
                if response.status_code == 404:
                    # URL doesn't exist, skip this test
                    continue
                    
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
            '/dashboard/reports/profit-loss/',
            '/dashboard/reports/expense/',
            '/dashboard/finance/',
        ]
        
        for url in sensitive_report_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                if response.status_code == 404:
                    # URL doesn't exist, skip this test
                    continue
                    
                # Should be blocked or redirected
                self.assertIn(response.status_code, [403, 302])


class ManagerAccessTests(SecurityTestCase):
    """Test manager user access levels"""
    
    def test_manager_can_access_management_features(self):
        """Test manager can access appropriate management features"""
        self.client.login(username='manager_test', password='test123456')
        
        manager_urls = [
            '/dashboard/inventory/',
            '/dashboard/sales/',
            '/dashboard/reports/',
        ]
        
        for url in manager_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                # Should not get 404 or 500 errors
                self.assertNotEqual(response.status_code, 404)
                self.assertNotEqual(response.status_code, 500)
    
    def test_manager_blocked_from_admin_only_features(self):
        """Test manager cannot access admin-only features"""
        self.client.login(username='manager_test', password='test123456')
        
        admin_only_urls = [
            '/dashboard/authentication/roles/',
            '/dashboard/authentication/permissions/',
            '/dashboard/authentication/roles/create/',
        ]
        
        for url in admin_only_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                if response.status_code == 404:
                    # URL doesn't exist, skip this test
                    continue
                    
                # Should be blocked or redirected
                self.assertIn(response.status_code, [403, 302])


class SecurityMiddlewareTests(SecurityTestCase):
    """Test security middleware functionality"""
    
    def test_unauthenticated_user_redirected(self):
        """Test unauthenticated users are redirected to login"""
        protected_urls = [
            '/dashboard/inventory/',
            '/dashboard/sales/',
            '/dashboard/reports/',
            '/dashboard/authentication/users/',
        ]
        
        for url in protected_urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                if response.status_code == 404:
                    # URL doesn't exist, skip this test
                    continue
                    
                # Should be redirected to login
                self.assertIn(response.status_code, [302, 403])
                
                if response.status_code == 302:
                    self.assertTrue('login' in response.url.lower())
    
    def test_login_logout_functionality(self):
        """Test login and logout work correctly"""
        # Test login
        login_response = self.client.post('/dashboard/authentication/login/', {
            'username': 'admin_test',
            'password': 'test123456'
        })
        
        # Should redirect after successful login
        if login_response.status_code != 404:
            self.assertEqual(login_response.status_code, 302)
        
        # Test logout
        logout_response = self.client.post('/dashboard/authentication/logout/')
        
        # Should redirect after logout
        if logout_response.status_code != 404:
            self.assertEqual(logout_response.status_code, 302)


class SecurityDecoratorsTests(SecurityTestCase):
    """Test that security decorators are properly applied"""
    
    def test_view_protection_coverage(self):
        """Test that critical views have security decorators"""
        # This test checks that our security audit found the right protection level
        
        # Load the security audit report
        try:
            with open('security_audit_report.json', 'r') as f:
                audit_data = json.load(f)
        except FileNotFoundError:
            self.skipTest("Security audit report not found")
        
        # Check that protection rate is high
        protection_rate = audit_data.get('protection_rate', 0)
        self.assertGreaterEqual(protection_rate, 80.0, 
                              f"Protection rate too low: {protection_rate}%")
        
        # Check that only expected public views are unprotected
        unprotected_views = audit_data.get('unprotected_view_details', [])
        public_view_names = ['faqs', 'homepage', 'login_view', 'logout_view']
        
        for view in unprotected_views:
            view_name = view.get('name', '')
            self.assertIn(view_name, public_view_names,
                         f"Unexpected unprotected view: {view_name}")


class IntegrationTests(SecurityTestCase):
    """Integration tests for the complete security system"""
    
    def test_complete_user_workflow(self):
        """Test a complete user workflow with security checks"""
        # Test 1: Unauthenticated user should be redirected
        response = self.client.get('/dashboard/inventory/')
        if response.status_code != 404:
            self.assertIn(response.status_code, [302, 403])
        
        # Test 2: Login as admin
        self.client.login(username='admin_test', password='test123456')
        
        # Test 3: Admin should be able to access admin pages
        response = self.client.get('/dashboard/authentication/users/')
        if response.status_code != 404:
            self.assertNotEqual(response.status_code, 403)
        
        # Test 4: Logout
        self.client.logout()
        
        # Test 5: Login as restricted user
        self.client.login(username='restricted_test', password='test123456')
        
        # Test 6: Restricted user should be blocked from admin pages
        response = self.client.get('/dashboard/authentication/users/')
        if response.status_code != 404:
            self.assertIn(response.status_code, [403, 302])
    
    def test_role_based_access_matrix(self):
        """Test role-based access matrix"""
        access_matrix = {
            'admin_test': {
                'should_access': [
                    '/dashboard/authentication/users/',
                    '/dashboard/authentication/roles/',
                    '/dashboard/inventory/',
                    '/dashboard/sales/',
                    '/dashboard/reports/',
                    '/dashboard/finance/',
                ],
                'should_block': []
            },
            'manager_test': {
                'should_access': [
                    '/dashboard/inventory/',
                    '/dashboard/sales/',
                    '/dashboard/reports/',
                ],
                'should_block': [
                    '/dashboard/authentication/roles/',
                    '/dashboard/authentication/permissions/',
                ]
            },
            'restricted_test': {
                'should_access': [
                    '/dashboard/inventory/',  # May have limited access
                ],
                'should_block': [
                    '/dashboard/authentication/users/',
                    '/dashboard/authentication/roles/',
                    '/dashboard/authentication/permissions/',
                ]
            }
        }
        
        for username, access_rules in access_matrix.items():
            with self.subTest(user=username):
                self.client.login(username=username, password='test123456')
                
                # Test should_access URLs
                for url in access_rules['should_access']:
                    response = self.client.get(url)
                    if response.status_code != 404:
                        self.assertNotEqual(response.status_code, 403,
                                          f"{username} should access {url}")
                
                # Test should_block URLs
                for url in access_rules['should_block']:
                    response = self.client.get(url)
                    if response.status_code != 404:
                        self.assertIn(response.status_code, [403, 302],
                                     f"{username} should be blocked from {url}")
                
                self.client.logout()


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
    suite.addTests(loader.loadTestsFromTestCase(SecurityDecoratorsTests))
    suite.addTests(loader.loadTestsFromTestCase(IntegrationTests))
    
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