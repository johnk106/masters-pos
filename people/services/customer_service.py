from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404,redirect
from people.models import Customer
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import uuid

class CustomerManager:

    @staticmethod
    def create_customer(request):
        code    = request.POST.get("code", "").strip()
        name    = request.POST.get("name", "").strip()
        email   = request.POST.get("email", "").strip()
        phone   = request.POST.get("phone", "").strip()
        country = request.POST.get("country", "").strip()
        status  = request.POST.get("status") == "on"
        image   = request.FILES.get("image")

        if not code:
            while True:
                candidate = uuid.uuid4().hex[:8].upper()
                if not Customer.objects.filter(code=candidate).exists():
                    code = candidate
                    break

        if not all([name, email, phone, country]):
            messages.error(request, 'All fields except image are required.')
            return redirect('people:customers')

        if Customer.objects.filter(code__iexact=code).exists():
            messages.error(request, f'Customer code "{code}" already exists.')
            return redirect('people:customers')

        customer = Customer.objects.create(
            code=code,
            name=name,
            email=email,
            phone=phone,
            country=country,
            status=status,
            created_by=request.user
        )
        if image:
            customer.image = image
            customer.save(update_fields=["image"])

        # 5) Flash a success message
        messages.success(request, f'Customer "{customer.name}" created successfully with code {customer.code}.')
        return redirect('people:customers')


    @staticmethod
    @login_required
    def edit_customer(request, customer_id):

        customer = get_object_or_404(Customer, id=customer_id)

        code    = request.POST.get("code", "").strip()
        name    = request.POST.get("name", "").strip()
        email   = request.POST.get("email", "").strip()
        phone   = request.POST.get("phone", "").strip()
        country = request.POST.get("country", "").strip()
        status  = request.POST.get("status") == "on"
        image   = request.FILES.get("image")

        if not all([code, name, email, phone, country]):
            messages.error(request,f'All fields except image are required.')
            return redirect('people:customers')

        if Customer.objects.exclude(id=customer_id).filter(code__iexact=code).exists():
            messages.error(request,f'Customer code "{code}" already exists.')
            return redirect('people:customers')

        customer.code    = code
        customer.name    = name
        customer.email   = email
        customer.phone   = phone
        customer.country = country
        customer.status  = status
        if image:
            customer.image = image
        customer.save()

        messages.success(request,f'Customer information updated succesfully')
        return redirect('people:customers')


    @staticmethod
    @login_required
    def delete_customer(request, customer_id):

        customer = get_object_or_404(Customer, id=customer_id)
        customer.delete()

        messages.success(request,f'Customer deleted succesfully')
        return redirect('people:customers')

