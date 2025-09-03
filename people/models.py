from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Supplier(models.Model):
    code = models.CharField(max_length=10)
    name = models.TextField()
    image = models.ImageField(upload_to='supplier_images/',null=True)
    email = models.EmailField()
    phone = models.TextField()
    country = models.TextField()
    status = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'{self.code} - {self.name}'
    

class Customer(models.Model):
    code = models.CharField(max_length=12)
    name = models.CharField(max_length=225)
    image = models.ImageField(upload_to='customer-images/')
    email = models.EmailField()
    phone = models.TextField()
    country = models.TextField()
    status = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,related_name='customers',on_delete=models.SET_NULL,null=True)


    def __str__(self):
        return self.name