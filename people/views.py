from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from .models import Supplier,Customer
from people.services.supplier_service import SupplierManager
from django.contrib import messages
from people.services.customer_service import CustomerManager
from authentication.decorators import manager_or_above
from django.contrib.auth.decorators import login_required
@manager_or_above

def suppliers_list(request):
    suppliers_qs = Supplier.objects.all().only('id', 'code', 'name', 'email', 'phone', 'country', 'status')
    paginator = Paginator(suppliers_qs, 10)  # Show 10 per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'people/suppliers.html', {
        'page_obj': page_obj,
    })
@manager_or_above

def create_supplier(request):
    if request.method == 'POST':
        return SupplierManager.create_supplier(request)

    messages.warning(request, "Method not allowed.")
    return redirect('people:suppliers')
@manager_or_above

def edit_supplier(request, supplier_id):
    if request.method == 'POST':
        return SupplierManager.edit_supplier(request, supplier_id)

    messages.warning(request, "Method not allowed.")
    return redirect('people:suppliers')
@manager_or_above

def delete_supplier(request, supplier_id):
    return SupplierManager.delete_supplier(request, supplier_id)
@login_required



def customers(request):
    qs = Customer.objects.select_related('created_by').order_by('-date_created')

    paginator = Paginator(qs, 25)
    page_number = request.GET.get('page')  
    page_obj = paginator.get_page(page_number)

    return render(request, 'people/customer.html', {
        'page_obj': page_obj,
    })
@login_required


def create_customer(request):
    if request.method != "POST":
            return redirect('people:customers')
   
    return CustomerManager.create_customer(request)
@login_required


def edit_customer(request, customer_id):
    if request.method != "POST":
            return redirect('people:customers')
   
    return CustomerManager.edit_customer(request, customer_id)
@login_required



def delete_customer(request, customer_id):
    if request.method != "POST":
            return redirect('people:customers')
  
    return CustomerManager.delete_customer(request, customer_id)