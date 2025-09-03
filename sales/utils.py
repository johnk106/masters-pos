import io
from django.http import FileResponse
from django.db.models import Q
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from decimal import Decimal

from .models import Order

# —————————————
# Query builder
# —————————————

def get_orders_queryset(search: str = None, source: str = None, customer: str = None, 
                       status: str = None, payment_status: str = None, sort_by: str = None):
    qs = Order.objects.all().select_related('customer', 'biller') \
                 .prefetch_related('items__product') \
                 .order_by('-id')
    
    if source:
        qs = qs.filter(source=source)
    
    if search:
        qs = qs.filter(
            Q(reference__icontains=search) |
            Q(customer__name__icontains=search) |
            Q(items__product__name__icontains=search)
        ).distinct()
    
    # Filter by customer
    if customer:
        qs = qs.filter(customer__name__icontains=customer)
    
    # Filter by status
    if status:
        qs = qs.filter(status=status)
    
    # Filter by payment status
    if payment_status:
        qs = qs.filter(payment_status=payment_status)
    
    # Apply sorting
    if sort_by:
        if sort_by == 'recently_added':
            qs = qs.order_by('-id')
        elif sort_by == 'ascending':
            qs = qs.order_by('reference')
        elif sort_by == 'descending':
            qs = qs.order_by('-reference')
        elif sort_by == 'last_month':
            from datetime import datetime, timedelta
            last_month = datetime.now() - timedelta(days=30)
            qs = qs.filter(date__gte=last_month.date()).order_by('-date')
        elif sort_by == 'last_7_days':
            from datetime import datetime, timedelta
            last_week = datetime.now() - timedelta(days=7)
            qs = qs.filter(date__gte=last_week.date()).order_by('-date')
    
    return qs

# —————————————
# Excel exporter
# —————————————

def export_orders_excel(qs, basename='orders'):
    wb = Workbook()
    ws = wb.active

    # header
    ws.append([
        'Reference', 'Date', 'Customer', 'Biller',
        'Status', 'Payment Status',
        'Grand Total', 'Paid', 'Due',
        'Items (Name × Qty)'
    ])

    # initialize running totals
    total_grand = Decimal('0.00')
    total_paid = Decimal('0.00')
    total_due = Decimal('0.00')

    for order in qs:
        items_desc = ", ".join(
            f"{item.product.name} ×{item.quantity}"
            for item in order.items.all()
        )

        # append the order row
        ws.append([
            order.reference,
            order.date.strftime('%Y-%m-%d'),
            order.customer.name if order.customer else 'walk in customer',
            order.biller.get_full_name() if order.biller else '',
            order.status.title(),
            order.payment_status.title(),
            f"Ksh {order.grand_total:,.2f}",
            f"Ksh {order.paid_amount:,.2f}",
            f"Ksh {order.due_amount:,.2f}",
            items_desc,
        ])

        # accumulate totals
        total_grand += order.grand_total
        total_paid  += order.paid_amount
        total_due   += order.due_amount

    # blank row for separation (optional)
    ws.append([])

    # totals row
    ws.append([
        'Totals',           # Reference column
        '',                 # Date
        '',                 # Customer
        '',                 # Biller
        '',                 # Status
        '',                 # Payment Status
        f"Ksh {total_grand:,.2f}",   # Grand Total sum
        f"Ksh {total_paid:,.2f}",    # Paid sum
        f"Ksh {total_due:,.2f}",     # Due sum
        ''                  # Items
    ])

    # create response
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return FileResponse(
        buf,
        as_attachment=True,
        filename=f'{basename}.xlsx'
    )


# —————————————
# PDF exporter
# —————————————

def export_orders_pdf(qs, basename='orders'):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 50

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"{basename.replace('-', ' ').title()} Report")
    y -= 30

    # Simplified headers
    c.setFont("Helvetica-Bold", 10)
    headers = ['Ref', 'Date', 'Cust', 'St', 'Total', 'Due']
    xs = [40, 100, 200, 300, 360, 450]
    for x, txt in zip(xs, headers):
        c.drawString(x, y, txt)
    y -= 15
    c.setFont("Helvetica", 9)

    # Totals accumulator
    total_grand = Decimal('0.00')
    total_due = Decimal('0.00')

    for order in qs:
        # new page if needed
        if y < 50:
            c.showPage()
            y = h - 50
            c.setFont("Helvetica-Bold", 10)
            for x, txt in zip(xs, headers):
                c.drawString(x, y, txt)
            y -= 15
            c.setFont("Helvetica", 9)

        # truncate ref and cust
        ref = order.reference[:6]
        cust = (order.customer.name or '')[:12] if order.customer else 'walk-in'

        vals = [
            ref,
            order.date.strftime('%Y-%m-%d'),
            cust,
            order.status[0].upper(),
            f"Ksh{order.grand_total:,.0f}",
            f"Ksh{order.due_amount:,.0f}",
        ]
        for x, text in zip(xs, vals):
            c.drawString(x, y, text)
        y -= 15

        # accumulate
        total_grand += order.grand_total
        total_due += order.due_amount

    # draw totals
    if y < 70:
        c.showPage()
        y = h - 50
    y -= 10
    c.setFont("Helvetica-Bold", 10)
    c.drawString(xs[0], y, 'Totals')
    c.drawString(xs[4], y, f"Ksh{total_grand:,.0f}")
    c.drawString(xs[5], y, f"Ksh{total_due:,.0f}")

    c.save()
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.pdf')

