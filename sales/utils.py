import io
from django.http import FileResponse, HttpResponse
from django.db.models import Q
from openpyxl import Workbook
from decimal import Decimal
from .models import Order

def get_orders_queryset(search=None):
    qs = Order.objects.all().select_related('customer')
    if search:
        qs = qs.filter(
            Q(reference__icontains=search) |
            Q(customer__name__icontains=search)
        )
    return qs.distinct()

def export_orders_excel(qs, basename='orders'):
    wb = Workbook()
    ws = wb.active
    ws.append(['Reference', 'Date', 'Customer', 'Status', 'Total'])
    for order in qs:
        ws.append([
            order.reference,
            order.date.strftime('%Y-%m-%d'),
            order.customer.name,
            order.status,
            float(order.total),
        ])
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'{basename}.xlsx')

def export_orders_pdf(qs, basename='orders'):
    return HttpResponse('PDF export temporarily disabled', status=503)
