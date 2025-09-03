from django.urls import path
from . import views

app_name='settings'
urlpatterns = [
    path('profile-settings/',views.profile_settings,name='profile-settings'),
    path('security-settings/',views.security_settings,name='security-settings')
]