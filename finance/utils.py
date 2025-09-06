import io
from django.http import FileResponse, HttpResponse
from openpyxl import Workbook

def export_finance_excel(qs, basename='finance'):
    wb = Workbook()
    ws = wb.active
    ws.append(['Date', 'Description', 'Amount', 'Type'])
    for item in qs:
        ws.append([
            item.date.strftime('%Y-%m-%d') if hasattr(item, 'date') else '',
            getattr(item, 'description', ''),
            float(getattr(item, 'amount', 0)),
            getattr(item, 'type', ''),
        ])
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'{basename}.xlsx')

def export_finance_pdf(qs, basename='finance'):
    return HttpResponse('PDF export temporarily disabled', status=503)
