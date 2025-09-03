from inventory.models import Category,SubCategory,Unit,Variant
from django.shortcuts import render,redirect
from django.utils.text import slugify
from django.contrib import messages

class CategoryManager:

    @staticmethod
    def create_category(request):
        try:
    
            name = request.POST.get('name','')
            slug = slugify(request.POST.get('slug',''))
            status = True

            new_category = Category.objects.create(
                name=name,
                slug=slug,
                status=status
            )
            print(new_category.name)

            messages.success(request,"New category created succesfully")

            return redirect('inventory:categories')
        
        except Exception as e:

            messages.error(request,f'An error occured during product creation:{e}')
            return redirect('inventory:categories')
        
    def edit_category(request,category_id):
        try:
            category = Category.objects.filter(id=category_id).first()
            if not category:
                messages.warning(request,"No category with that id could be found")

                return redirect('inventory:categories')
            

            category.name = request.POST.get('name','')
            category.slug = slugify(request.POST.get('slug',''))

            category.save()

            messages.success(request,"Category updated successfully")

            return redirect('inventory:categories')

        except Exception as e:
            print(e)

            messages.error(request,f'An error occured:{e}')

            return redirect('inventory:categories')
        
    def delete_category(request,category_id):
        try:
            category = Category.objects.get(pk=category_id)

            category.delete()

            messages.success(request,"Category deleted succesfully")

            return redirect('inventory:categories')

        except Exception as e:
            messages.error(request,f"An error occured:{e}")

            return redirect('inventory:categories')
            

        
class SubCategoryManager:
    @staticmethod
    def create_subcategory(request):
        try:
            category_id = request.POST.get('category')
            name = request.POST.get('name', '')
            slug = slugify(request.POST.get('slug', name))
            image = request.FILES.get('image')
            description = request.POST.get('description','')

            category = Category.objects.filter(id=category_id).first()

            SubCategory.objects.create(
                category=category,
                name=name,
                slug=slug,
                image=image,
                description=description,status=True
            )

            messages.success(request, "New sub-category created successfully")
            return redirect('inventory:sub-categories')
        except Exception as e:
            messages.error(request, f'An error occured during sub-category creation: {e}')
            return redirect('inventory:sub-categories')

    @staticmethod
    def edit_subcategory(request, subcategory_id):
        try:
            subcategory = SubCategory.objects.filter(id=subcategory_id).first()
            if not subcategory:
                messages.warning(request, "No sub-category with that id could be found")
                return redirect('inventory:sub-categories')

            subcategory.category_id = request.POST.get('category', subcategory.category_id)
            subcategory.name = request.POST.get('name', subcategory.name)
            subcategory.slug = slugify(request.POST.get('slug', subcategory.slug))
            if 'image' in request.FILES:
                subcategory.image = request.FILES['image']
            subcategory.save()

            messages.success(request, "Sub-category updated successfully")
            return redirect('inventory:sub-categories')
        except Exception as e:
            messages.error(request, f'An error occured during sub-category update: {e}')
            return redirect('inventory:sub-categories')

    @staticmethod
    def delete_subcategory(request, subcategory_id):
        try:
            subcategory = SubCategory.objects.get(pk=subcategory_id)
            subcategory.delete()

            messages.success(request, "Sub-category deleted successfully")
            return redirect('inventory:sub-categories')
        except Exception as e:
            messages.error(request, f"An error occured during sub-category deletion: {e}")
            return redirect('inventory:sub-categories')


class UnitManager:
    @staticmethod
    def create_unit(request):
        try:
            name = request.POST.get('name', '')
            short_name = request.POST.get('short_name', '')
            status = request.POST.get('status') == 'on'

            Unit.objects.create(
                name=name,
                short_name=short_name,
                status=status
            )

            messages.success(request, "New unit created successfully")
            return redirect('inventory:units')
        except Exception as e:
            messages.error(request, f'An error occured during unit creation: {e}')
            return redirect('inventory:units')

    @staticmethod
    def edit_unit(request, unit_id):
        try:
            unit = Unit.objects.filter(id=unit_id).first()
            if not unit:
                messages.warning(request, "No unit with that id could be found")
                return redirect('inventory:units')

            unit.name = request.POST.get('name', unit.name)
            unit.short_name = request.POST.get('short_name', unit.short_name)
            unit.status = request.POST.get('status') == 'on'
            unit.save()

            messages.success(request, "Unit updated successfully")
            return redirect('inventory:units')
        except Exception as e:
            messages.error(request, f'An error occured during unit update: {e}')
            return redirect('inventory:units')

    @staticmethod
    def delete_unit(request, unit_id):
        try:
            unit = Unit.objects.get(pk=unit_id)
            unit.delete()

            messages.success(request, "Unit deleted successfully")
            return redirect('inventory:units')
        except Exception as e:
            messages.error(request, f"An error occured during unit deletion: {e}")
            return redirect('inventory:units')


class VariantManager:
    @staticmethod
    def create_variant(request):
        try:
            name = request.POST.get('name', '')
            values = request.POST.get('values', '')
            # status = request.POST.get('status') == 'on'

            status = True

            Variant.objects.create(
                name=name,
                values=values,
                status=status
            )

            messages.success(request, "New variant created successfully")
            return redirect('inventory:variants')
        except Exception as e:
            messages.error(request, f'An error occured during variant creation: {e}')
            return redirect('inventory:variants')

    @staticmethod
    def edit_variant(request, variant_id):
        try:
            variant = Variant.objects.filter(id=variant_id).first()
            if not variant:
                messages.warning(request, "No variant with that id could be found")
                return redirect('inventory:variants')

            variant.name = request.POST.get('name', variant.name)
            variant.values = request.POST.get('values', variant.values)
            variant.status = request.POST.get('status') == 'on'
            variant.save()

            messages.success(request, "Variant updated successfully")
            return redirect('inventory:variants')
        except Exception as e:
            messages.error(request, f'An error occured during variant update: {e}')
            return redirect('inventory:variants')

    @staticmethod
    def delete_variant(request, variant_id):
        try:
            variant = Variant.objects.get(pk=variant_id)
            variant.delete()

            messages.success(request, "Variant deleted successfully")
            return redirect('inventory:variants')
        except Exception as e:
            messages.error(request, f"An error occured during variant deletion: {e}")
            return redirect('inventory:variants')

