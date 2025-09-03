from django.urls import path
from . import views

app_name = "people"
urlpatterns = [
    
    path('suppliers/', views.suppliers_list, name='suppliers'),
    path('suppliers/create/', views.create_supplier, name='create-supplier'),
    path('suppliers/<int:supplier_id>/edit/', views.edit_supplier, name='edit_supplier'),
    path('suppliers/<int:supplier_id>/delete/', views.delete_supplier, name='delete_supplier'),
    path('customers/',views.customers, name='customers'),
    path('customers/create/',views.create_customer,name='create-customer'),
    path('customers/<int:customer_id>/edit/',views.edit_customer,name='edit-customer'),
    path('customers/<int:customer_id>/delete/',views.delete_customer,name='delete-customer'),

]