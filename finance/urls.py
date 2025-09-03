from django.urls import path
from . import views

app_name = "finance"
urlpatterns = [
    path('expenses/',views.expenses,name='expenses'),
    path('create-expense/',views.expense_create,name='create-expense'),
    path('edit-expense/<int:expense_id>/',views.expense_edit,name='edit-expense'),
    path('delete-expense/<int:expense_id>/',views.expense_delete,name='delete-expense'),
    path('expense-categories/',views.expense_categories,name='expense-categories'),
    path('create-expense-category/',views.expense_category_create,name='create-expense-category'),
    path('edit-expense-category/<int:category_id>/',views.expense_category_edit,name='edit-expense-category'),
    path('delete-expense-category/<int:category_id>/',views.expense_category_delete,name='delete-expense-category')

]