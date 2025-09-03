from django.core.management.base import BaseCommand
from django.test import Client
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Test error handling functionality'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Error Handling System'))
        self.stdout.write('=' * 50)
        
        # Create a test client
        client = Client()
        
        # Test 1: Check if error templates exist
        self.stdout.write('\n1. Checking error templates...')
        
        template_400 = os.path.join(settings.BASE_DIR, 'templates', '400.html')
        template_500 = os.path.join(settings.BASE_DIR, 'templates', '500.html')
        
        if os.path.exists(template_400):
            self.stdout.write(self.style.SUCCESS('   ✓ 400.html template exists'))
        else:
            self.stdout.write(self.style.ERROR('   ✗ 400.html template missing'))
            
        if os.path.exists(template_500):
            self.stdout.write(self.style.SUCCESS('   ✓ 500.html template exists'))
        else:
            self.stdout.write(self.style.ERROR('   ✗ 500.html template missing'))
        
        # Test 2: Check templates directory in settings
        self.stdout.write('\n2. Checking Django settings...')
        
        templates_dirs = settings.TEMPLATES[0]['DIRS']
        if templates_dirs and any('templates' in str(dir_path) for dir_path in templates_dirs):
            self.stdout.write(self.style.SUCCESS('   ✓ Templates directory configured in settings'))
        else:
            self.stdout.write(self.style.ERROR('   ✗ Templates directory not configured in settings'))
        
        # Test 3: Check DEBUG setting
        self.stdout.write('\n3. Checking DEBUG setting...')
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING('   ⚠ DEBUG is True - Error pages will not display'))
            self.stdout.write('     Set DEBUG=False in production to see custom error pages')
        else:
            self.stdout.write(self.style.SUCCESS('   ✓ DEBUG is False - Error pages will display'))
        
        # Test 4: Check error handlers
        self.stdout.write('\n4. Checking error handlers...')
        
        # Import the main URLconf
        from django.urls import get_resolver
        resolver = get_resolver()
        
        if hasattr(resolver, 'handler400'):
            self.stdout.write(self.style.SUCCESS('   ✓ Custom 400 handler configured'))
        else:
            self.stdout.write(self.style.ERROR('   ✗ Custom 400 handler not configured'))
            
        if hasattr(resolver, 'handler500'):
            self.stdout.write(self.style.SUCCESS('   ✓ Custom 500 handler configured'))
        else:
            self.stdout.write(self.style.ERROR('   ✗ Custom 500 handler not configured'))
        
        # Test 5: Test error URLs (if DEBUG is False)
        if not settings.DEBUG:
            self.stdout.write('\n5. Testing error URLs...')
            
            try:
                response = client.get('/test/500/')
                if response.status_code == 500:
                    self.stdout.write(self.style.SUCCESS('   ✓ 500 error page working'))
                else:
                    self.stdout.write(self.style.ERROR(f'   ✗ 500 error page returned status {response.status_code}'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ✗ Error testing 500 page: {e}'))
        
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Error handling system verification complete!'))
        
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING('\nTo fully test error pages:'))
            self.stdout.write('1. Set DEBUG=False in admin/admin/settings.py')
            self.stdout.write('2. Run: python manage.py collectstatic --noinput')
            self.stdout.write('3. Visit /test/500/ or /test/400/ to see error pages')
            self.stdout.write('4. Remember to remove test URLs in production!')