from django.http import FileResponse
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
import io
from openpyxl import Workbook
# from reportlab.lib.pagesizes import A4  # Temporarily disabled
# from reportlab.pdfgen import canvas  # Temporarily disabled

def _export_purchases_excel(purchase_qs, basename='purchases'):
    wb = Workbook()
    ws = wb.active
    ws.append(['PO Reference', 'Date', 'Supplier', 'Product', 'Quantity', 'Unit Price', 'Discount', 'Tax', 'Line Total'])
    
    for purchase in purchase_qs:
        for item in purchase.items.all():
            ws.append([
                purchase.reference,
                purchase.order_date.strftime('%Y-%m-%d'),
                purchase.supplier.name,
                item.product.name,
                item.quantity,
                float(item.unit_price),
                float(item.discount_amount),
                float(item.tax_amount),
                float(item.line_total),
            ])
    
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    filename = f"{basename}.xlsx"
    return FileResponse(buffer, as_attachment=True, filename=filename)

def _export_purchases_pdf(purchase_qs, basename='purchases'):
    """PDF export temporarily disabled"""
    from django.http import HttpResponse
    return HttpResponse("PDF export temporarily disabled", status=503)
