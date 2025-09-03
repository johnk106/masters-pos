from django.urls import path
from . import views

app_name = "purchases"
urlpatterns = [
    path('',views.purchases,name='purchases'),
    path('ajax/products/', views.get_products_ajax, name='get_products_ajax'),
    path('ajax/purchase/<int:purchase_id>/', views.get_purchase_details_ajax, name='get_purchase_details_ajax'),
    path('edit/<int:purchase_id>/', views.edit_purchase, name='edit_purchase'),
]