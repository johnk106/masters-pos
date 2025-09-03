from django.urls import path
from . import views

app_name = "sales"
urlpatterns = [
    path('online-orders/',views.online_orders,name='online-orders'),
    path('pos-orders/',views.pos_orders,name='pos-orders'),
    path('sales-returns/',views.sales_return,name='sales-returns'),
    path('pos/',views.pos,name='pos'),
    path('create-order/',views.create_order,name='create-order'),
    path('orders/<int:pk>/json/', views.order_detail_json, name='order-detail-json'),
    path('orders/<int:order_id>/update-payment/', views.update_payment, name='update-payment'),
    path('customers/ajax/', views.get_customers_ajax, name='customers-ajax'),
    path('cash-register-data/', views.cash_register_data, name='cash-register-data'),
    path('today-profit-data/', views.today_profit_data, name='today-profit-data'),
    
    # M-Pesa endpoints
    path('initiate-mpesa-payment/', views.initiate_mpesa_payment, name='initiate-mpesa-payment'),
    path('mpesa-callback/', views.mpesa_callback, name='mpesa-callback'),
    path('check-mpesa-status/<str:checkout_request_id>/', views.check_mpesa_status, name='check-mpesa-status'),
    path('mpesa-transactions/', views.mpesa_transactions, name='mpesa-transactions'),
    path('mpesa-status/', views.mpesa_system_status, name='mpesa-status'),
    path('order-status/<int:order_id>/', views.order_status, name='order-status'),
]