from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from people.models import Supplier

class SupplierManager:

    @staticmethod
    def create_supplier(request):
        try:
            code = request.POST.get('code', '').strip()
            name = request.POST.get('name', '').strip()
            image = request.FILES.get('image', None)
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            country = request.POST.get('country', '').strip()

            Supplier.objects.create(
                code=code,
                name=name,
                image=image,
                email=email,
                phone=phone,
                country=country
            )

            messages.success(request, "Supplier created successfully.")
        except Exception as e:
            messages.error(request, f"Failed to create supplier: {e}")

        return redirect('people:suppliers')

    @staticmethod
    def edit_supplier(request, supplier_id):
        try:
            supplier = get_object_or_404(Supplier, id=supplier_id)

            supplier.code = request.POST.get('code', '').strip()
            supplier.name = request.POST.get('name', '').strip()
            supplier.email = request.POST.get('email', '').strip()
            supplier.phone = request.POST.get('phone', '').strip()
            supplier.country = request.POST.get('country', '').strip()

            if 'image' in request.FILES:
                supplier.image = request.FILES['image']

            supplier.save()
            messages.success(request, "Supplier updated successfully.")
        except Exception as e:
            messages.error(request, f"Failed to update supplier: {e}")

        return redirect('people:suppliers')

    @staticmethod
    def delete_supplier(request, supplier_id):
        try:
            supplier = get_object_or_404(Supplier, id=supplier_id)
            supplier.delete()
            messages.success(request, "Supplier deleted successfully.")
        except Exception as e:
            messages.error(request, f"Failed to delete supplier: {e}")

        return redirect('people:suppliers')
