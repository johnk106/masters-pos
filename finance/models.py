from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class ExpenseCategory(models.Model):
    name = models.TextField()
    description = models.TextField()
    status = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

class Expense(models.Model):
    name = models.TextField()
    description = models.TextField()
    category = models.ForeignKey(ExpenseCategory,on_delete=models.SET_NULL,related_name='expenses',null=True)
    date = models.TextField()
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount in Ksh"
    )
    status = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User,related_name='expenses',on_delete=models.SET_NULL,null=True)

    def __str__(self):
        return self.name