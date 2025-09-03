from inventory.models import Category,SubCategory,Unit,Variant
from django.shortcuts import render,redirect
from django.utils.text import slugify
from django.contrib import messages
from inventory.models import Product,Stock,ProductGallery

class ProductManager:
    @staticmethod
    def create_product(request):
        try:
            # Product fields
            name = request.POST.get('name', '')
            # Remove slug and sku from form processing - they will be auto-generated
            selling_type = request.POST.get('selling_type', '')
            category_id = request.POST.get('category', None)
            sub_category_id = request.POST.get('sub_category', None)
            unit_id = request.POST.get('unit', None)
            description = request.POST.get('description', '')
            purchase_price = request.POST.get('purchase_price', '0')

            # Create Product - slug and sku will be auto-generated in save method
            product = Product.objects.create(
                name=name,
                selling_type=selling_type,
                category_id=category_id,
                sub_category_id=sub_category_id,
                units_id=unit_id,
                description=description,
                purchase_price=purchase_price
            )

            # Stock fields
            quantity = int(request.POST.get('quantity', 0))
            price = request.POST.get('price', '0')
            tax_type = request.POST.get('tax_type', '')
            tax = int(request.POST.get('tax', 0))
            discount_type = request.POST.get('discount_type', '')
            discount = int(request.POST.get('discount', 0))
            quantity_alert = int(request.POST.get('quantity_alert', 0))

            # Create Stock entry
            Stock.objects.create(
                product=product,
                quantity=quantity,
                price=price,
                tax_type=tax_type,
                tax=tax,
                discount_type=discount_type,
                discount=discount,
                quantity_alert=quantity_alert
            )

            # Gallery images (multiple)
            for img in request.FILES.getlist('images'):
                ProductGallery.objects.create(product=product, image=img)

            messages.success(request, "Product and stock created successfully.")
            return redirect('inventory:product-list')
        except Exception as e:
            messages.error(request, f"Error creating product: {e}")
            return redirect('inventory:product-list')

    @staticmethod
    def edit_product(request, product_id):
        try:
            product = Product.objects.get(pk=product_id)
            # Update fields
            product.name = request.POST.get('name', product.name)
            # Keep existing slug and sku handling for edit
            product.slug = slugify(request.POST.get('slug', product.slug))
            product.sku = request.POST.get('sku', product.sku)
            product.selling_type = request.POST.get('selling_type', product.selling_type)
            product.category_id = request.POST.get('category', product.category_id)
            product.sub_category_id = request.POST.get('sub_category', product.sub_category_id)
            product.units_id = request.POST.get('unit', product.units_id)
            product.description = request.POST.get('description', product.description)
            product.purchase_price = request.POST.get('purchase_price', product.purchase_price)
            product.save()

            # Update Stock: assume single stock entry
            stock = product.stock_entries.first()
            if stock:
                stock.quantity = int(request.POST.get('quantity', stock.quantity))
                stock.price = request.POST.get('price', stock.price)
                stock.tax_type = request.POST.get('tax_type', stock.tax_type)
                stock.tax = int(request.POST.get('tax', stock.tax))
                stock.discount_type = request.POST.get('discount_type', stock.discount_type)
                stock.discount = int(request.POST.get('discount', stock.discount))
                stock.quantity_alert = int(request.POST.get('quantity_alert', stock.quantity_alert))
                stock.save()

            # Handle new gallery images if any
            for img in request.FILES.getlist('images'):
                ProductGallery.objects.create(product=product, image=img)

            messages.success(request, "Product updated successfully.")
            return redirect('inventory:product-list')
        except Product.DoesNotExist:
            messages.error(request, "Product not found.")
            return redirect('inventory:product-list')
        except Exception as e:
            messages.error(request, f"Error updating product: {e}")
            return redirect('inventory:product-list')

    @staticmethod
    def delete_product(request, product_id):
        try:
            product = Product.objects.get(pk=product_id)
            product.delete()
            messages.success(request, "Product deleted successfully.")
        except Product.DoesNotExist:
            messages.error(request, "Product not found.")
        except Exception as e:
            messages.error(request, f"Error deleting product: {e}")
        return redirect('inventory:product-list')


