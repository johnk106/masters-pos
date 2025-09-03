import io
from decimal import Decimal
from django.http import FileResponse
from openpyxl import Workbook
from django.db.models import Sum, Value
from django.db.models.functions import Coalesce
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def export_expenses_excel(qs, basename='expenses'):
    """
    Export a QuerySet of Expense instances to Excel.
    """
    wb = Workbook()
    ws = wb.active

    # Header row
    ws.append([
        'Name', 'Description', 'Category',
        'Date', 'Amount', 'Status',
        'Created By', 'Date Created'
    ])

    # Data rows
    for exp in qs:
        ws.append([
            exp.name,
            exp.description,
            exp.category.name if exp.category else '',
            exp.date,
            f"ksh {Decimal(exp.amount):,.2f}",
            exp.status,
            exp.created_by.username if exp.created_by else '',
            exp.date_created.strftime('%Y-%m-%d %H:%M'),
        ])

    # Totals row (sum of amounts)
    total_amount = qs.aggregate(
        total=Coalesce(Sum('amount_decimal'), Value(0))
    )['total'] if False else sum(Decimal(e.amount) for e in qs)
    ws.append([])
    ws.append(['TOTAL', '', '', '', f"{total_amount:,.2f}", '', '', ''])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f"{basename}.xlsx")


def export_expenses_pdf(qs, basename='expenses'):
    """
    Export a QuerySet of Expense instances to PDF.
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
    headers = ['Name',  'Cat', 'Date', 'Amt', 'Status', 'By', ]
    xs = [40, 140, 260, 320, 380, 440, 480, 540]
    c.setFont("Helvetica-Bold", 10)
    for x, txt in zip(xs, headers):
        c.drawString(x, y, txt)
    y -= 15
    c.setFont("Helvetica", 9)

    # Data rows
    for exp in qs:
        if y < 50:
            c.showPage()
            y = h - 50
            c.setFont("Helvetica-Bold", 10)
            for x, txt in zip(xs, headers):
                c.drawString(x, y, txt)
            y -= 15
            c.setFont("Helvetica", 9)

        vals = [
            exp.name[:12],
            (exp.category.name if exp.category else '')[:7],
            exp.date,
            f"ksh {Decimal(exp.amount):.0f}",
            exp.status[:10],
            (exp.created_by.username if exp.created_by else '')[:6],
        ]
        for x, txt in zip(xs, vals):
            c.drawString(x, y, txt)
        y -= 12

    # Total
    total_amount = sum(Decimal(e.amount) for e in qs)
    if y < 70:
        c.showPage()
        y = h - 70
    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(xs[0], y, "TOTAL")
    c.drawString(xs[4], y, f"ksh {total_amount:.0f}")

    c.save()
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f"{basename}.pdf")