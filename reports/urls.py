from django.urls import path
from . import views


app_name = 'reports'
urlpatterns = [
    path('sales-reports/',views.sales_report,name='sales-report'),
    path('best-sellers/',views.best_sellers,name='best-sellers'),
    path('purchase-report/',views.purchase_report,name='purchase-report'),
    path('inventory-report/',views.inventory_report,name='inventory-report'),
    path('stock-history/',views.stock_history,name='stock-history'),
    path('sold-stock/',views.sold_stock,name='sold-stock'),
    path('expense-report/',views.expense_report,name='expense-report'),
    path('profit-loss-report/',views.profit_loss_report,name='profit-loss-report'),
    path('opening-inventory/',views.opening_inventory_report,name='opening-inventory-report')
]