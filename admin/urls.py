"""
URL configuration for admin project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from .error_handlers import custom_400_view, custom_500_view
from .test_views import test_400_error, test_500_error

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/homepage',include('landing.urls')),
    path('dashboard/inventory/',include('inventory.urls')),
    path('dashboard/purchases/',include('purchases.urls')),
    path('dashboard/sales/',include('sales.urls')),
    path('dashboard/finance/',include('finance.urls')),
    path('dashboard/people/',include('people.urls')),
    path('dashboard/reports/',include('reports.urls')),
    path('dashboard/content/',include('content.urls')),
    path('dashboard/authentication/',include('authentication.urls')),
    path('dashboard/settings/',include('settings.urls')),
    # Test error URLs (remove in production)
    path('test/400/', test_400_error, name='test_400'),
    path('test/500/', test_500_error, name='test_500')

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler400 = custom_400_view
handler500 = custom_500_view
