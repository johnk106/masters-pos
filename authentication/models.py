# models.py

from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.models import Permission as DjangoPermission

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    permissions = models.ManyToManyField(DjangoPermission, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    def get_color_class(self):
        """Return CSS class for role color coding"""
        color_map = {
            'Admin': 'bg-danger',
            'Manager': 'bg-primary', 
            'Salesman': 'bg-success',
            'Supervisor': 'bg-warning',
            'Store Keeper': 'bg-info',
            'Inventory Manager': 'bg-secondary'
        }
        return color_map.get(self.name, 'bg-secondary')

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='userprofile')
    phone = models.CharField(max_length=20, blank=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} Profile"
    
    def get_role_name(self):
        return self.role.name if self.role else 'No Role'
    
    def get_role_color_class(self):
        return self.role.get_color_class() if self.role else 'bg-secondary'
