# reports/utils.py
import io
from django.http import FileResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from decimal import Decimal

def format_currency(amount):
    """Format currency with thousand separators"""
    if amount is None:
        amount = 0
    return f"ksh {amount:,.2f}"

def export_sales_excel(report_rows, basename='sales_report'):
    """
    Exports a list (or ValuesQuerySet) of dicts with keys:
      'sku', 'name', 'category', 'sold_qty', 'sold_amount'
    """
    wb = Workbook()
    ws = wb.active
    # Header
    ws.append(['SKU', 'Name', 'Category', 'Sold Qty', 'Sold Amount'])

    # Data rows
    total_qty = 0
    total_amount = 0
    for row in report_rows:
        qty = row.get('sold_qty') or 0
        amt = row.get('sold_amount') or 0
        total_qty += qty
        total_amount += amt
        ws.append([
            row.get('sku', ''),
            row.get('name', ''),
            row.get('category', ''),
            f"{qty:,}",  # Format quantity with thousand separators
            format_currency(amt),
        ])

    # Totals row
    ws.append([])
    ws.append(['TOTAL', '', '', f"{total_qty:,}", format_currency(total_amount)])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.xlsx')


def export_sales_pdf(report_rows, basename='sales_report'):
    """
    Exports sales report to PDF 
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 50

    # Title
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, basename.replace('_', ' ').title())
    y -= 30

    # Headers
    headers = ['SKU', 'Name', 'Category', 'Sold Qty', 'Amount']
    x_positions = [40, 120, 240, 340, 420]

    c.setFont("Helvetica-Bold", 10)
    for x, header in zip(x_positions, headers):
        c.drawString(x, y, header)
    y -= 15

    # Data rows
    c.setFont("Helvetica", 9)
    total_qty = 0
    total_amount = 0

    for row in report_rows:
        if y < 50:  # Start new page if needed
            c.showPage()
            y = height - 50
            c.setFont("Helvetica-Bold", 10)
            for x, header in zip(x_positions, headers):
                c.drawString(x, y, header)
            y -= 15
            c.setFont("Helvetica", 9)

        qty = row.get('sold_qty') or 0
        amt = row.get('sold_amount') or 0
        total_qty += qty
        total_amount += amt

        values = [
            row.get('sku', '')[:12],
            row.get('name', '')[:20],
            row.get('category', '')[:15],
            f"{qty:,}",
            format_currency(amt)
        ]

        for x, val in zip(x_positions, values):
            c.drawString(x, y, str(val))
        y -= 12

    # Totals
    if y < 70:
        c.showPage()
        y = height - 70
    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_positions[0], y, "TOTAL")
    c.drawString(x_positions[3], y, f"{total_qty:,}")
    c.drawString(x_positions[4], y, format_currency(total_amount))

    c.save(); buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.pdf')




def export_purchase_report_excel(products, basename='purchase_report'):
    """
    Exports annotated Product list with purchase_quantity and purchase_amount to Excel.
    Each item: sku, name, category, purchase_quantity, purchase_amount
    """
    wb=Workbook(); ws=wb.active
    ws.append(['SKU','Name','Category','Purchase Qty','Purchase Amount'])
    total_amount=Decimal('0.00')
    total_quantity=0
    for p in products:
        amt=p.purchase_amount or Decimal('0.00')
        qty=p.purchase_quantity or 0
        total_amount+=amt
        total_quantity+=qty
        ws.append([p.sku, p.name, p.category.name if p.category else '', f"{qty:,}", format_currency(amt)])
    ws.append([])
    ws.append(['TOTAL','', '', f"{total_quantity:,}", format_currency(total_amount)])
    buf=io.BytesIO(); wb.save(buf); buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.xlsx')


def export_purchase_report_pdf(products, basename='purchase_report'):
    buf=io.BytesIO(); c=canvas.Canvas(buf, pagesize=A4); w,h=A4; y=h-50
    c.setFont("Helvetica-Bold",14); c.drawString(40,y, basename.replace('_',' ').title()); y-=30
    headers=['SKU','Name','Cat','Qty','Amt']; xs=[40,140,240,320,400]
    c.setFont("Helvetica-Bold",10)
    for x,txt in zip(xs,headers): c.drawString(x,y,txt)
    y-=15; c.setFont("Helvetica",9)
    total_amount=Decimal('0.00')
    total_quantity=0
    for p in products:
        if y<50: c.showPage(); y=h-50; c.setFont("Helvetica-Bold",10)
        for x,txt in zip(xs,headers): c.drawString(x,y,txt)
        y-=15; c.setFont("Helvetica",9)
        amt=p.purchase_amount or Decimal('0.00')
        qty=p.purchase_quantity or 0
        total_amount+=amt
        total_quantity+=qty
        vals=[p.sku, p.name[:15], (p.category.name if p.category else '')[:8], f"{qty:,}", format_currency(amt)]
        for x,txt in zip(xs,vals): c.drawString(x,y,txt)
        y-=12
    if y<70: c.showPage(); y=h-70
    y-=20; c.setFont("Helvetica-Bold",10)
    c.drawString(xs[0],y,"TOTAL"); c.drawString(xs[3],y,f"{total_quantity:,}"); c.drawString(xs[4],y,format_currency(total_amount))
    c.save(); buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.pdf')



def export_inventory_excel(products, basename='inventory_report'):
    wb = Workbook()
    ws = wb.active
    ws.append(['SKU', 'Name', 'Category', 'Unit', 'Stock'])

    for p in products:
        # Get the stock value properly
        stock_value = ''
        try:
            stock = p.stock() if callable(p.stock) else p.stock
            stock_value = stock.quantity if hasattr(stock, 'quantity') else stock
        except Exception:
            stock_value = ''

        ws.append([
            getattr(p, 'sku', ''),
            p.name,
            p.category.name if hasattr(p, 'category') and p.category else '',
            p.units.name if hasattr(p, 'units') and p.units else '',
            stock_value,
        ])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.xlsx')


def export_inventory_pdf(products, basename='inventory_report'):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, basename.replace('_', ' ').title())
    y -= 30

    headers = ['SKU', 'Name', 'Category', 'Unit', 'Stock']
    xs = [40, 120, 240, 340, 420]

    def draw_headers():
        c.setFont("Helvetica-Bold", 10)
        for x, txt in zip(xs, headers):
            c.drawString(x, y, txt)

    draw_headers()
    y -= 15
    c.setFont("Helvetica", 9)

    for p in products:
        if y < 50:
            c.showPage()
            y = h - 50
            draw_headers()
            y -= 15
            c.setFont("Helvetica", 9)

        # Get the stock value properly
        stock_value = ''
        try:
            stock = p.stock() if callable(p.stock) else p.stock
            stock_value = str(stock.quantity) if hasattr(stock, 'quantity') else str(stock)
        except Exception:
            stock_value = '0'

        vals = [
            getattr(p, 'sku', '')[:12],
            p.name[:20],
            (p.category.name if hasattr(p, 'category') and p.category else '')[:15],
            (p.units.name if hasattr(p, 'units') and p.units else '')[:10],
            stock_value,
        ]

        for x, txt in zip(xs, vals):
            c.drawString(x, y, txt)
        y -= 12

    c.save()
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.pdf')

def export_expense_excel(expenses, basename='expense_report'):
    wb = Workbook()
    ws = wb.active
    ws.append(['Date', 'Category', 'Description', 'Amount', 'Recorded By'])

    total_amount = Decimal('0.00')
    for exp in expenses:
        # Convert amount from text to decimal for proper formatting
        try:
            amount = Decimal(str(exp.amount).replace(',', '').replace('ksh', '').strip())
            total_amount += amount
            formatted_amount = format_currency(amount)
        except (ValueError, TypeError, AttributeError):
            formatted_amount = f'ksh {str(exp.amount)}'
        
        ws.append([
            str(exp.date),
            exp.category.name if exp.category else '',
            exp.description,
            formatted_amount,
            exp.created_by.get_full_name() if exp.created_by else '',
        ])

    # Add total row
    ws.append([])
    ws.append(['TOTAL', '', '', format_currency(total_amount), ''])

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.xlsx')


def export_expense_pdf(expenses, basename='expense_report'):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, basename.replace('_', ' ').title())
    y -= 30

    headers = ['Date', 'Category', 'Description', 'Amount', 'Recorded By']
    xs = [40, 110, 200, 340, 460]

    def draw_headers():
        c.setFont("Helvetica-Bold", 10)
        for x, txt in zip(xs, headers):
            c.drawString(x, y, txt)

    draw_headers()
    y -= 15
    c.setFont("Helvetica", 9)

    total_amount = Decimal('0.00')
    for exp in expenses:
        if y < 50:
            c.showPage()
            y = h - 50
            draw_headers()
            y -= 15
            c.setFont("Helvetica", 9)

        # Convert amount from text to decimal for proper formatting
        try:
            amount = Decimal(str(exp.amount).replace(',', '').replace('ksh', '').strip())
            total_amount += amount
            formatted_amount = format_currency(amount)
        except (ValueError, TypeError, AttributeError):
            formatted_amount = f'ksh {str(exp.amount)}'

        vals = [
            str(exp.date)[:10],
            (exp.category.name if exp.category else '')[:15],
            exp.description[:25],
            formatted_amount,
            (exp.created_by.get_full_name() if exp.created_by else '')[:15]
        ]
        for x, txt in zip(xs, vals):
            c.drawString(x, y, txt)
        y -= 12

    # Add total row
    if y < 70:
        c.showPage()
        y = h - 70
    y -= 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(xs[0], y, "TOTAL")
    c.drawString(xs[3], y, format_currency(total_amount))

    c.save()
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.pdf')


def export_profit_loss_excel(context, basename='profit_loss_report'):
    """
    Exports profit/loss report data to Excel.
    """
    wb = Workbook()
    ws = wb.active
    
    month_labels = context['month_labels']
    
    # Header row
    header = ['Category'] + month_labels
    ws.append(header)
    
    # Income Section
    ws.append(['Income'] + [''] * len(month_labels))
    
    # Sales row
    sales_row = ['Sales'] + [format_currency(v) for v in context['sales']]
    ws.append(sales_row)
    
    # Service row
    service_row = ['Service'] + [format_currency(v) for v in context['services']]
    ws.append(service_row)
    
    # Purchase Return row
    purchase_return_row = ['Purchase Return'] + [format_currency(v) for v in context['purchase_returns']]
    ws.append(purchase_return_row)
    
    # Gross Profit row
    gross_profit_row = ['Gross Profit'] + [format_currency(v) for v in context['gross_profit']]
    ws.append(gross_profit_row)
    
    # Empty row
    ws.append([''] * (len(month_labels) + 1))
    
    # Expenses Section
    ws.append(['Expenses'] + [''] * len(month_labels))
    
    # Purchase row
    purchase_row = ['Purchase'] + [format_currency(v) for v in context['purchases']]
    ws.append(purchase_row)
    
    # Operating Expenses row
    expenses_row = ['Operating Expenses'] + [format_currency(v) for v in context['expenses']]
    ws.append(expenses_row)
    
    # Sales Return row
    sales_return_row = ['Sales Return'] + [format_currency(v) for v in context['sales_returns']]
    ws.append(sales_return_row)
    
    # Total Expense row
    total_expense_row = ['Total Expense'] + [format_currency(v) for v in context['total_expense']]
    ws.append(total_expense_row)
    
    # Empty row
    ws.append([''] * (len(month_labels) + 1))
    
    # Net Profit row
    net_profit_row = ['Net Profit'] + [format_currency(v) for v in context['net_profit']]
    ws.append(net_profit_row)
    
    # Style the header row
    from openpyxl.styles import Font, PatternFill
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
    
    # Style section headers and totals
    bold_font = Font(bold=True)
    for row in [2, 7, 9, 13, 15]:  # Income, Expenses, Gross Profit, Total Expense, Net Profit
        if row <= ws.max_row:
            for cell in ws[row]:
                cell.font = bold_font
    
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.xlsx')


def export_profit_loss_pdf(context, basename='profit_loss_report'):
    """
    Exports profit/loss report data to PDF.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 50
    
    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Profit & Loss Report")
    y -= 40
    
    month_labels = context['month_labels']
    
    # Calculate column positions
    col_width = 70
    start_x = 40
    label_width = 120
    xs = [start_x] + [start_x + label_width + (i * col_width) for i in range(len(month_labels))]
    
    # Header row
    c.setFont("Helvetica-Bold", 10)
    c.drawString(xs[0], y, "Category")
    for i, label in enumerate(month_labels):
        if i < len(xs) - 1:  # Prevent index out of range
            c.drawString(xs[i + 1], y, label[:8])  # Truncate long month labels
    y -= 20
    
    c.setFont("Helvetica", 9)
    
    # Income Section
    c.setFont("Helvetica-Bold", 10)
    c.drawString(xs[0], y, "Income")
    y -= 15
    c.setFont("Helvetica", 9)
    
    # Sales
    c.drawString(xs[0], y, "Sales")
    for i, v in enumerate(context['sales']):
        if i < len(xs) - 1:
            c.drawString(xs[i + 1], y, format_currency(v)[:10])
    y -= 12
    
    # Service
    c.drawString(xs[0], y, "Service")
    for i, v in enumerate(context['services']):
        if i < len(xs) - 1:
            c.drawString(xs[i + 1], y, format_currency(v)[:10])
    y -= 12
    
    # Purchase Return
    c.drawString(xs[0], y, "Purchase Return")
    for i, v in enumerate(context['purchase_returns']):
        if i < len(xs) - 1:
            c.drawString(xs[i + 1], y, format_currency(v)[:10])
    y -= 12
    
    # Gross Profit
    c.setFont("Helvetica-Bold", 9)
    c.drawString(xs[0], y, "Gross Profit")
    for i, v in enumerate(context['gross_profit']):
        if i < len(xs) - 1:
            c.drawString(xs[i + 1], y, format_currency(v)[:10])
    y -= 20
    
    # Expenses Section
    c.setFont("Helvetica-Bold", 10)
    c.drawString(xs[0], y, "Expenses")
    y -= 15
    c.setFont("Helvetica", 9)
    
    # Purchase
    c.drawString(xs[0], y, "Purchase")
    for i, v in enumerate(context['purchases']):
        if i < len(xs) - 1:
            c.drawString(xs[i + 1], y, format_currency(v)[:10])
    y -= 12
    
    # Operating Expenses
    c.drawString(xs[0], y, "Operating Expenses")
    for i, v in enumerate(context['expenses']):
        if i < len(xs) - 1:
            c.drawString(xs[i + 1], y, format_currency(v)[:10])
    y -= 12
    
    # Sales Return
    c.drawString(xs[0], y, "Sales Return")
    for i, v in enumerate(context['sales_returns']):
        if i < len(xs) - 1:
            c.drawString(xs[i + 1], y, format_currency(v)[:10])
    y -= 12
    
    # Total Expense
    c.setFont("Helvetica-Bold", 9)
    c.drawString(xs[0], y, "Total Expense")
    for i, v in enumerate(context['total_expense']):
        if i < len(xs) - 1:
            c.drawString(xs[i + 1], y, format_currency(v)[:10])
    y -= 20
    
    # Net Profit
    c.setFont("Helvetica-Bold", 10)
    c.drawString(xs[0], y, "Net Profit")
    for i, v in enumerate(context['net_profit']):
        if i < len(xs) - 1:
            c.drawString(xs[i + 1], y, format_currency(v)[:10])
    
    c.save()
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.pdf')


def export_opening_inventory_excel(report_rows, basename='opening_inventory_report'):
    """
    Exports opening inventory report to Excel
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Opening Inventory Report"
    
    # Header
    headers = ['Product Name', 'Category', 'Unit', 'Opening Qty', 'Sold Qty', 'Closing Qty']
    ws.append(headers)

    # Data rows
    total_opening = 0
    total_sold = 0
    total_closing = 0
    
    for row in report_rows:
        opening_qty = row.get('opening_qty', 0)
        sold_qty = row.get('sold_qty', 0)
        closing_qty = row.get('closing_qty', 0)
        
        total_opening += opening_qty
        total_sold += sold_qty
        total_closing += closing_qty
        
        ws.append([
            row.get('product_name', ''),
            row.get('category', ''),
            row.get('unit', ''),
            opening_qty,
            sold_qty,
            closing_qty,
        ])

    # Totals row
    ws.append([])
    ws.append(['TOTAL', '', '', total_opening, total_sold, total_closing])

    # Format numbers with thousand separators
    for row in ws.iter_rows(min_row=2, max_col=6):
        for col_idx, cell in enumerate(row):
            if col_idx >= 3 and cell.value is not None:  # Quantity columns
                if isinstance(cell.value, (int, float)):
                    cell.number_format = '#,##0'

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.xlsx')


def export_opening_inventory_pdf(report_rows, basename='opening_inventory_report'):
    """
    Exports opening inventory report to PDF
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    width, height = A4
    y = height - 50

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Opening Inventory Report")
    y -= 40

    # Headers
    headers = ['Product Name', 'Category', 'Unit', 'Opening Qty', 'Sold Qty', 'Closing Qty']
    x_positions = [40, 160, 240, 290, 360, 430]

    c.setFont("Helvetica-Bold", 10)
    for x, header in zip(x_positions, headers):
        c.drawString(x, y, header)
    y -= 20

    # Data rows
    c.setFont("Helvetica", 9)
    total_opening = 0
    total_sold = 0
    total_closing = 0

    for row in report_rows:
        if y < 100:  # Start new page if needed
            c.showPage()
            y = height - 50
            c.setFont("Helvetica-Bold", 16)
            c.drawString(40, y, "Opening Inventory Report (continued)")
            y -= 40
            
            c.setFont("Helvetica-Bold", 10)
            for x, header in zip(x_positions, headers):
                c.drawString(x, y, header)
            y -= 20
            c.setFont("Helvetica", 9)

        opening_qty = row.get('opening_qty', 0)
        sold_qty = row.get('sold_qty', 0)
        closing_qty = row.get('closing_qty', 0)
        
        total_opening += opening_qty
        total_sold += sold_qty
        total_closing += closing_qty

        values = [
            row.get('product_name', '')[:18],
            row.get('category', '')[:12],
            row.get('unit', '')[:8],
            f"{opening_qty:,}",
            f"{sold_qty:,}",
            f"{closing_qty:,}"
        ]

        for x, value in zip(x_positions, values):
            c.drawString(x, y, str(value))
        y -= 15

    # Totals row
    y -= 10
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_positions[0], y, "TOTAL")
    c.drawString(x_positions[3], y, f"{total_opening:,}")
    c.drawString(x_positions[4], y, f"{total_sold:,}")
    c.drawString(x_positions[5], y, f"{total_closing:,}")

    c.save()
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{basename}.pdf')

