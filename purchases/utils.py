from django.http import FileResponse
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
import io
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def _export_purchases_excel(purchase_qs, basename='purchases'):
    """
    Expects purchase_qs = Purchase.objects.select_related('supplier').prefetch_related('items__product')
    """
    wb = Workbook()
    ws = wb.active

    # Header
    ws.append([
        'PO Ref', 'Order Date', 'Supplier',
        'Product', 'Qty', 'Unit Cost',
        'Discount', 'Tax Amt', 'Line Total'
    ])

    # Rows
    for purchase in purchase_qs:
        for item in purchase.items.all():
            ws.append([
                purchase.reference,
                purchase.order_date.strftime('%Y-%m-%d'),
                purchase.supplier.name,
                item.product.name,
                item.quantity,
                f"{item.unit_cost:.2f}",
                f"{item.discount:.2f}",
                f"{item.tax_amount:.2f}",
                f"{item.total_cost:.2f}",
            ])

    # Grand totals (quantity & value across all items)
    # Build a flat list of all items
    all_items = [item for p in purchase_qs for item in p.items.all()]
    total_qty = sum(item.quantity for item in all_items)
    total_value = sum(item.total_cost for item in all_items)

    ws.append([])
    ws.append([
        'TOTAL', '', '',
        '', total_qty, '',
        '', '',
        f"{total_value:.2f}",
    ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.xlsx')


def _export_purchases_pdf(purchase_qs, basename='purchases'):
    """
    Expects purchase_qs = Purchase.objects.select_related('supplier').prefetch_related('items__product')
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 50

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"{basename.replace('-', ' ').title()} Report")
    y -= 30

    # Column headers
    headers = ['PO Ref', 'Date', 'Supp', 'Prod', 'Qty', 'Unit', 'Disc', 'Tax', 'Line Tot']
    xs = [40, 100, 160, 220, 320, 360, 400, 440, 480]
    c.setFont("Helvetica-Bold", 10)
    for x, txt in zip(xs, headers):
        c.drawString(x, y, txt)
    y -= 15
    c.setFont("Helvetica", 9)

    # Data rows
    for purchase in purchase_qs:
        for item in purchase.items.all():
            if y < 50:
                c.showPage()
                y = h - 50
                c.setFont("Helvetica-Bold", 10)
                for x, txt in zip(xs, headers):
                    c.drawString(x, y, txt)
                y -= 15
                c.setFont("Helvetica", 9)

            vals = [
                purchase.reference,
                purchase.order_date.strftime('%Y-%m-%d'),
                purchase.supplier.name[:8],
                item.product.name[:10],
                str(item.quantity),
                f"{item.unit_cost:.0f}",
                f"{item.discount:.0f}",
                f"{item.tax_amount:.0f}",
                f"{item.total_cost:.0f}",
            ]
            for x, txt in zip(xs, vals):
                c.drawString(x, y, txt)
            y -= 12

    # Grand totals
    all_items = [item for p in purchase_qs for item in p.items.all()]
    total_qty = sum(item.quantity for item in all_items)
    total_value = sum(item.total_cost for item in all_items)

    if y < 70:
        c.showPage()
        y = h - 70
    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(xs[0], y, "TOTAL")
    c.drawString(xs[4], y, str(total_qty))
    c.drawString(xs[-1], y, f"{total_value:.0f}")

    c.save()
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.pdf')
