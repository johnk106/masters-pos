from django.urls import path
from . import views

app_name = 'landing'
urlpatterns = [
    path('',views.homepage,name='homepage'),
    path('sales-dashboard/',views.sales_dashboard,name="sales-dashboard")

]