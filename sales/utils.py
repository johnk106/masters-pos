import io
from django.http import FileResponse, HttpResponse
from django.db.models import Q
from openpyxl import Workbook
from decimal import Decimal
from .models import Order

def get_orders_queryset(search=None, source=None, customer=None, status=None, payment_status=None, sort_by=None, include_failed=False):
    qs = Order.objects.all().select_related('customer')
    
    # By default, exclude failed orders unless explicitly requested
    if not include_failed:
        qs = qs.exclude(status=Order.Status.FAILED)
    
    # Filter by search term
    if search:
        qs = qs.filter(
            Q(reference__icontains=search) |
            Q(customer__name__icontains=search)
        )
    
    # Filter by source
    if source:
        qs = qs.filter(source=source)
    
    # Filter by customer
    if customer:
        qs = qs.filter(customer_id=customer)
    
    # Filter by status
    if status:
        qs = qs.filter(status=status)
    
    # Filter by payment status
    if payment_status:
        qs = qs.filter(payment_status=payment_status)
    
    # Apply sorting
    if sort_by:
        if sort_by == 'date_asc':
            qs = qs.order_by('date')
        elif sort_by == 'date_desc':
            qs = qs.order_by('-date')
        elif sort_by == 'total_asc':
            qs = qs.order_by('grand_total')
        elif sort_by == 'total_desc':
            qs = qs.order_by('-grand_total')
        elif sort_by == 'customer':
            qs = qs.order_by('customer__name')
        else:
            qs = qs.order_by('-date')  # Default sort
    else:
        qs = qs.order_by('-date')  # Default sort by newest first
    
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
