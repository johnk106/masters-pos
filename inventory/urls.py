from django.urls import path
from . import views

app_name = "inventory"
urlpatterns = [
    path('product-list/',views.product_list,name="product-list"),
    path('create-product/',views.create_product,name="create-product"),
    path('edit-product/<int:product_id>/',views.edit_product,name="edit-product"),
    path('delete-product/<int:product_id>/',views.delete_product,name='delete-product'),
    path('view-product/<int:product_id>/',views.product_details,name="product-details"),
    path('low-stocks/',views.low_stocks,name='low-stocks'),
    path('categories/',views.categories,name="categories"),
    path('create-category/',views.create_category,name="create-category"),
    path('edit-category/<int:category_id>/',views.edit_category,name='edit-category'),
    path('delete-category/<int:category_id>/',views.delete_category,name='delete-category'),
    path('sub-categories/',views.sub_categories,name="sub-categories"),
    path('create-subcategory/',views.create_subcategory,name='create-subcategory'),
    path('edit-subcategory/<int:subcategory_id>/',views.edit_subcategory,name='edit-subcategory'),
    path('delete-subcategory/<int:subcategory_id>/',views.delete_subcategory,name='delete-subcategory'),
    path('units/',views.units,name='units'),
    path('create-units/',views.create_unit,name='create-unit'),
    path('edit-unit/<int:unit_id>/',views.edit_unit,name='edit-unit'),
    path('delete-unit/<int:unit_id>/',views.delete_unit,name="delete-unit"),
    path('variants/',views.variants,name='variants'),
    path('create-variant/',views.create_variant,name="create-variant"),
    path('edit-variant/<int:variant_id>/',views.edit_variant,name='edit-variant'),
    path('delete-variant/<int:variant_id>/',views.delete_variant,name='delete-variant'),
    # AJAX endpoints
    path('ajax/create-category/',views.ajax_create_category,name='ajax-create-category'),
    path('ajax/create-subcategory/',views.ajax_create_subcategory,name='ajax-create-subcategory'),
    path('ajax/get-subcategories/',views.ajax_get_subcategories,name='ajax-get-subcategories'),
]