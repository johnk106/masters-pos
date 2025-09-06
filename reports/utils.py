import io
from django.http import FileResponse, HttpResponse
from openpyxl import Workbook

def export_report_excel(qs, basename='report'):
    wb = Workbook()
    ws = wb.active
    ws.append(['Item', 'Value', 'Date'])
    for item in qs:
        ws.append([
            str(item),
            getattr(item, 'value', ''),
            getattr(item, 'date', '').strftime('%Y-%m-%d') if hasattr(item, 'date') else '',
        ])
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'{basename}.xlsx')

def export_report_pdf(qs, basename='report'):
    return HttpResponse('PDF export temporarily disabled', status=503)
