from django.shortcuts import render
from datetime import datetime
from django.shortcuts          import render
from django.db.models         import Sum, F, Q
from sales.models                  import Order, OrderItem
from inventory.models         import Product,Unit,Category
from finance.models import Expense,ExpenseCategory
from django.core.paginator  import Paginator
from django.db.models import Sum, Value,DecimalField
from django.db.models.functions import Coalesce,ExtractMonth, ExtractYear,Cast
from decimal import Decimal
from datetime import date
from purchases.models import Purchase
from sales.models import *
from django.db.models import DateField
from .utils import *
from authentication.decorators import manager_or_above
from django.contrib.auth.decorators import login_required
@login_required

# Create your views here.
def sales_report(request):
    # --- 1) Parse filters from GET ---
    date_range = request.GET.get('date_range', '').strip()
    start_date = end_date = None
    error_message = None
    
    if date_range:
        try:
            start_str, end_str = date_range.split(' - ')
            start_str = start_str.strip()
            end_str = end_str.strip()
            
            # Try both formats: dd/mm/yyyy (from date picker) and dd-mm-yyyy (alternative)
            date_formats = ['%d/%m/%Y', '%d-%m-%Y']
            
            for date_format in date_formats:
                try:
                    start_date = datetime.strptime(start_str, date_format).date()
                    end_date = datetime.strptime(end_str, date_format).date()
                    break
                except ValueError:
                    continue
            
            if not start_date or not end_date:
                raise ValueError("Invalid date format")
            
            # Validate date range
            if start_date > end_date:
                error_message = "Start date must be before or equal to end date."
                start_date = end_date = None
                
        except (ValueError, AttributeError):
            error_message = "Invalid date format. Please use the date picker to select dates."
            start_date = end_date = None

    selected_store   = request.GET.get('store',   'All')
    selected_product = request.GET.get('product', 'All')

    # --- 2) Base QS: only COMPLETED orders ---
    orders = Order.objects.filter(status=Order.Status.COMPLETED)

    if start_date and end_date:
        orders = orders.filter(date__range=(start_date, end_date))
    if selected_store != 'All':
        orders = orders.filter(store__name=selected_store)
    if selected_product != 'All':
        orders = orders.filter(items__product__name=selected_product)
    orders = orders.distinct()

    # --- 3) Summary cards ---
    summary = orders.aggregate(
        total_amount=Sum('grand_total'),
        total_paid=  Sum('paid_amount'),
        total_unpaid=Sum('due_amount'),
        overdue=      Sum(
            'due_amount',
            filter=Q(payment_status__in=[Order.PaymentStatus.UNPAID, Order.PaymentStatus.PARTIAL])
        ),
    )
    summary = {k: (v or 0) for k, v in summary.items()}

    # --- 4) Per-product report table ---
    report_rows = (
        OrderItem.objects
        .filter(order__in=orders)
        .select_related('product')
        .values(
            sku      = F('product__sku'),
            name     = F('product__name'),
            category = F('product__category__name'),
        )
        .annotate(
            sold_qty    = Sum('quantity'),
            sold_amount = Sum('total_cost'),
        )
        .order_by('-sold_amount')
    )

    products = Product.objects.values_list('name', flat=True).order_by('name')

    # Generate filename suffix for exports
    filename_suffix = ""
    if start_date and end_date:
        filename_suffix = f"_{start_date.strftime('%d-%m-%Y')}_to_{end_date.strftime('%d-%m-%Y')}"

    # Handle exports
    exp = request.GET.get('export')
    if exp == 'excel':
        return export_sales_excel(report_rows, f'sales_report{filename_suffix}')
    if exp == 'pdf':
        return export_sales_pdf(report_rows, f'sales_report{filename_suffix}')

    # Paginate report_rows
    paginator = Paginator(report_rows, 25)
    page_obj  = paginator.get_page(request.GET.get('page', 1))

    # Build export URLs with current filters
    export_params = {}
    if date_range:
        export_params['date_range'] = date_range
    if selected_store != 'All':
        export_params['store'] = selected_store
    if selected_product != 'All':
        export_params['product'] = selected_product
    
    from urllib.parse import urlencode
    export_query_string = urlencode(export_params)
    export_excel_url = f'?export=excel&{export_query_string}' if export_query_string else '?export=excel'
    export_pdf_url = f'?export=pdf&{export_query_string}' if export_query_string else '?export=pdf'

    return render(request, 'reports/sales-report.html', {
        'total_amount':   summary['total_amount'],
        'total_paid':     summary['total_paid'],
        'total_unpaid':   summary['total_unpaid'],
        'overdue':        summary['overdue'],
        'report_rows':    page_obj,
        'products':       ['All', *products],
        'selected_store': selected_store,
        'selected_product': selected_product,
        'date_range':     date_range,
        'error_message':  error_message,
        'export_excel_url': export_excel_url,
        'export_pdf_url':   export_pdf_url,
    })
@login_required



def best_sellers(request):
    # Parse date range from GET parameters
    date_range = request.GET.get('date_range', '').strip()
    start_date = end_date = None
    error_message = None
    
    if date_range:
        try:
            start_str, end_str = date_range.split(' - ')
            start_str = start_str.strip()
            end_str = end_str.strip()
            
            # Try both formats: dd/mm/yyyy (from date picker) and dd-mm-yyyy (alternative)
            date_formats = ['%d/%m/%Y', '%d-%m-%Y']
            
            for date_format in date_formats:
                try:
                    start_date = datetime.strptime(start_str, date_format).date()
                    end_date = datetime.strptime(end_str, date_format).date()
                    break
                except ValueError:
                    continue
            
            if not start_date or not end_date:
                raise ValueError("Invalid date format")
            
            # Validate date range
            if start_date > end_date:
                error_message = "Start date must be before or equal to end date."
                start_date = end_date = None
                
        except (ValueError, AttributeError):
            error_message = "Invalid date format. Please use the date picker to select dates."
            start_date = end_date = None

    # Base QS annotated with optional date filtering
    qs = Product.objects.select_related('category')
    
    if start_date and end_date:
        qs = qs.annotate(
            sold_qty=Sum(
                'order_items__quantity',
                filter=Q(order_items__order__status=Order.Status.COMPLETED) &
                       Q(order_items__order__date__range=(start_date, end_date))
            ),
            sold_amount=Sum(
                'order_items__total_cost',
                filter=Q(order_items__order__status=Order.Status.COMPLETED) &
                       Q(order_items__order__date__range=(start_date, end_date))
            )
        )
    else:
        qs = qs.annotate(
            sold_qty=Sum(
                'order_items__quantity',
                filter=Q(order_items__order__status=Order.Status.COMPLETED)
            ),
            sold_amount=Sum(
                'order_items__total_cost',
                filter=Q(order_items__order__status=Order.Status.COMPLETED)
            )
        )
    
    qs = qs.order_by('-sold_qty')
    top_30 = list(qs[:30])

    # Generate filename suffix for exports
    filename_suffix = ""
    if start_date and end_date:
        filename_suffix = f"_{start_date.strftime('%d-%m-%Y')}_to_{end_date.strftime('%d-%m-%Y')}"

    # Handle exports
    exp = request.GET.get('export')
    if exp == 'excel':
        return export_best_sellers_excel(top_30, f'best_sellers{filename_suffix}')
    if exp == 'pdf':
        return export_best_sellers_pdf(top_30, f'best_sellers{filename_suffix}')

    # Build export URLs with current filters
    export_params = {}
    if date_range:
        export_params['date_range'] = date_range
    
    from urllib.parse import urlencode
    export_query_string = urlencode(export_params)
    export_excel_url = f'?export=excel&{export_query_string}' if export_query_string else '?export=excel'
    export_pdf_url = f'?export=pdf&{export_query_string}' if export_query_string else '?export=pdf'

    # Paginate
    paginator = Paginator(top_30, 10)
    page_obj  = paginator.get_page(request.GET.get('page', 1))
    
    return render(request, 'reports/best-sellers.html', {
        'page_obj': page_obj,
        'date_range': date_range,
        'error_message': error_message,
        'export_excel_url': export_excel_url,
        'export_pdf_url': export_pdf_url,
    })
@manager_or_above


def purchase_report(request):
    # --- 1) Parse filters from GET ---
    date_range = request.GET.get('date_range', '').strip()
    start_date = end_date = None
    error_message = None
    
    if date_range:
        try:
            start_str, end_str = date_range.split(' - ')
            start_str = start_str.strip()
            end_str = end_str.strip()
            
            # Try both formats: dd/mm/yyyy (from date picker) and dd-mm-yyyy (alternative)
            date_formats = ['%d/%m/%Y', '%d-%m-%Y']
            
            for date_format in date_formats:
                try:
                    start_date = datetime.strptime(start_str, date_format).date()
                    end_date = datetime.strptime(end_str, date_format).date()
                    break
                except ValueError:
                    continue
            
            if not start_date or not end_date:
                raise ValueError("Invalid date format")
            
            # Validate date range
            if start_date > end_date:
                error_message = "Start date must be before or equal to end date."
                start_date = end_date = None
                
        except (ValueError, AttributeError):
            error_message = "Invalid date format. Please use the date picker to select dates."
            start_date = end_date = None

    # --- 2) Filter purchases based on date range ---
    purchase_filter = Q()
    if start_date and end_date:
        purchase_filter = Q(purchaseitem__purchase__order_date__range=(start_date, end_date))

    # Annotate purchase_amount and purchase_quantity per product
    products = (
        Product.objects
        .select_related('category')
        .annotate(
            purchase_amount=Coalesce(
                Sum('purchaseitem__total_cost', filter=purchase_filter),
                Value(Decimal('0.00'))
            ),
            purchase_quantity=Coalesce(
                Sum('purchaseitem__quantity', filter=purchase_filter),
                Value(0)
            )
        )
    )

    # Generate filename suffix for exports
    filename_suffix = ""
    if start_date and end_date:
        filename_suffix = f"_{start_date.strftime('%d-%m-%Y')}_to_{end_date.strftime('%d-%m-%Y')}"

    # Handle exports
    exp = request.GET.get('export')
    if exp == 'excel':
        return export_purchase_report_excel(products, f'purchase_report{filename_suffix}')
    if exp == 'pdf':
        return export_purchase_report_pdf(products, f'purchase_report{filename_suffix}')

    # Build export URLs with current filters
    export_params = {}
    if date_range:
        export_params['date_range'] = date_range
    
    from urllib.parse import urlencode
    export_query_string = urlencode(export_params)
    export_excel_url = f'?export=excel&{export_query_string}' if export_query_string else '?export=excel'
    export_pdf_url = f'?export=pdf&{export_query_string}' if export_query_string else '?export=pdf'

    return render(request, 'reports/purchase-report.html', {
        'products': products,
        'date_range': date_range,
        'error_message': error_message,
        'export_excel_url': export_excel_url,
        'export_pdf_url': export_pdf_url,
    })
@login_required

def inventory_report(request):
    # --- 1) Parse filters from GET ---
    date_range = request.GET.get('date_range', '').strip()
    start_date = end_date = None
    error_message = None
    
    if date_range:
        try:
            start_str, end_str = date_range.split(' - ')
            start_str = start_str.strip()
            end_str = end_str.strip()
            
            # Try both formats: dd/mm/yyyy (from date picker) and dd-mm-yyyy (alternative)
            date_formats = ['%d/%m/%Y', '%d-%m-%Y']
            
            for date_format in date_formats:
                try:
                    start_date = datetime.strptime(start_str, date_format).date()
                    end_date = datetime.strptime(end_str, date_format).date()
                    break
                except ValueError:
                    continue
            
            if not start_date or not end_date:
                raise ValueError("Invalid date format")
            
            # Validate date range
            if start_date > end_date:
                error_message = "Start date must be before or equal to end date."
                start_date = end_date = None
                
        except (ValueError, AttributeError):
            error_message = "Invalid date format. Please use the date picker to select dates."
            start_date = end_date = None

    # Base products queryset - inventory report shows all products regardless of date range
    # Date range filter is applied to related data if needed in the future
    products = (
        Product.objects
               .select_related('category','units')
               .all()
    )
    categories = Category.objects.all()
    units = Unit.objects.all()

    # Generate filename suffix for exports
    filename_suffix = ""
    if start_date and end_date:
        filename_suffix = f"_{start_date.strftime('%d-%m-%Y')}_to_{end_date.strftime('%d-%m-%Y')}"

    # Handle exports
    exp = request.GET.get('export')
    if exp == 'excel':
        return export_inventory_excel(products, f'inventory_report{filename_suffix}')
    if exp == 'pdf':
        return export_inventory_pdf(products, f'inventory_report{filename_suffix}')

    # Build export URLs with current filters
    export_params = {}
    if date_range:
        export_params['date_range'] = date_range
    
    from urllib.parse import urlencode
    export_query_string = urlencode(export_params)
    export_excel_url = f'?export=excel&{export_query_string}' if export_query_string else '?export=excel'
    export_pdf_url = f'?export=pdf&{export_query_string}' if export_query_string else '?export=pdf'

    return render(request, 'reports/inventory-report.html', {
        'products': products,
        'categories': categories,
        'units': units,
        'date_range': date_range,
        'error_message': error_message,
        'export_excel_url': export_excel_url,
        'export_pdf_url': export_pdf_url,
    })
@login_required


def stock_history(request):
    return render(request,'reports/stock-history.html',{})
@login_required

def sold_stock(request):
    return render(request,'reports/sold-stock.html',{})
@manager_or_above

def expense_report(request):
    # --- 1) Parse filters from GET ---
    date_range = request.GET.get('date_range', '').strip()
    start_date = end_date = None
    error_message = None
    
    if date_range:
        try:
            start_str, end_str = date_range.split(' - ')
            start_str = start_str.strip()
            end_str = end_str.strip()
            
            # Try both formats: dd/mm/yyyy (from date picker) and dd-mm-yyyy (alternative)
            date_formats = ['%d/%m/%Y', '%d-%m-%Y']
            
            for date_format in date_formats:
                try:
                    start_date = datetime.strptime(start_str, date_format).date()
                    end_date = datetime.strptime(end_str, date_format).date()
                    break
                except ValueError:
                    continue
            
            if not start_date or not end_date:
                raise ValueError("Invalid date format")
            
            # Validate date range
            if start_date > end_date:
                error_message = "Start date must be before or equal to end date."
                start_date = end_date = None
                
        except (ValueError, AttributeError):
            error_message = "Invalid date format. Please use the date picker to select dates."
            start_date = end_date = None

    # Base queryset with related data
    qs = (
        Expense.objects
        .select_related('category', 'created_by')
        .order_by('-date_created')
    )

    # Apply date filter if provided - Note: Expense.date is a TextField, need to handle carefully
    if start_date and end_date and not error_message:
        # Since date is stored as TextField, we need to filter by date_created instead
        # Or convert the text date field if it follows a consistent format
        qs = qs.filter(date_created__date__range=(start_date, end_date))

    # Generate filename suffix for exports
    filename_suffix = ""
    if start_date and end_date:
        filename_suffix = f"_{start_date.strftime('%d-%m-%Y')}_to_{end_date.strftime('%d-%m-%Y')}"

    # Export logic
    exp = request.GET.get('export')
    if exp == 'excel':
        return export_expense_excel(qs, f'expense_report{filename_suffix}')
    if exp == 'pdf':
        return export_expense_pdf(qs, f'expense_report{filename_suffix}')

    # Build export URLs with current filters
    export_params = {}
    if date_range:
        export_params['date_range'] = date_range
    
    from urllib.parse import urlencode
    export_query_string = urlencode(export_params)
    export_excel_url = f'?export=excel&{export_query_string}' if export_query_string else '?export=excel'
    export_pdf_url = f'?export=pdf&{export_query_string}' if export_query_string else '?export=pdf'

    # Pagination
    paginator = Paginator(qs, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    return render(request, 'reports/expense-report.html', {
        'page_obj': page_obj,
        'date_range': date_range,
        'error_message': error_message,
        'export_excel_url': export_excel_url,
        'export_pdf_url': export_pdf_url,
    })
@manager_or_above



def profit_loss_report(request):
    """
    Renders profit/loss report for all available months based on actual data range or custom date range.
    Aggregates sales, services, purchases, expenses per month.
    """
    from django.db.models import Min, Max
    from dateutil.relativedelta import relativedelta
    from django.contrib import messages
    
    # Parse custom date range from GET parameters
    date_range = request.GET.get('date_range', '').strip()
    custom_start_date = None
    custom_end_date = None
    error_message = None
    
    if date_range:
        try:
            start_str, end_str = date_range.split(' - ')
            start_str = start_str.strip()
            end_str = end_str.strip()
            
            # Try both formats: dd/mm/yyyy (from date picker) and dd-mm-yyyy (alternative)
            date_formats = ['%d/%m/%Y', '%d-%m-%Y']
            custom_start_date = None
            custom_end_date = None
            
            for date_format in date_formats:
                try:
                    custom_start_date = datetime.strptime(start_str, date_format).date()
                    custom_end_date = datetime.strptime(end_str, date_format).date()
                    break
                except ValueError:
                    continue
            
            if not custom_start_date or not custom_end_date:
                raise ValueError("Invalid date format")
            
            # Validate date range
            if custom_start_date > custom_end_date:
                error_message = "Start date must be before or equal to end date."
                custom_start_date = None
                custom_end_date = None
                
        except (ValueError, AttributeError):
            error_message = "Invalid date format. Please use the date picker to select dates."
            custom_start_date = None
            custom_end_date = None
    
    # If custom dates are provided and valid, use them; otherwise find data range
    if custom_start_date and custom_end_date:
        start_date = custom_start_date
        end_date = custom_end_date
        
        # Check if any data exists in the selected range
        orders_in_range = Order.objects.filter(date__range=[start_date, end_date]).exists()
        invoices_in_range = Invoice.objects.filter(created_at__date__range=[start_date, end_date]).exists()
        purchases_in_range = Purchase.objects.filter(order_date__range=[start_date, end_date]).exists()
        expenses_in_range = Expense.objects.annotate(
            date_dt=Cast('date', DateField())
        ).filter(date_dt__range=[start_date, end_date]).exists()
        
        has_data_in_range = orders_in_range or invoices_in_range or purchases_in_range or expenses_in_range
    else:
        # Find the earliest and latest dates across all data sources
        order_dates = Order.objects.aggregate(
            min_date=Min('date'),
            max_date=Max('date')
        )
        
        invoice_dates = Invoice.objects.aggregate(
            min_date=Min('created_at__date'),
            max_date=Max('created_at__date')
        )
        
        purchase_dates = Purchase.objects.aggregate(
            min_date=Min('order_date'),
            max_date=Max('order_date')
        )
        
        # Cast expense date field and get min/max
        expense_dates = Expense.objects.annotate(
            date_dt=Cast('date', DateField())
        ).aggregate(
            min_date=Min('date_dt'),
            max_date=Max('date_dt')
        )
        
        # Collect all dates that are not None
        all_dates = []
        for dates_dict in [order_dates, invoice_dates, purchase_dates, expense_dates]:
            if dates_dict['min_date']:
                all_dates.append(dates_dict['min_date'])
            if dates_dict['max_date']:
                all_dates.append(dates_dict['max_date'])
        
        # If no data exists, default to current year
        if not all_dates:
            current_year = date.today().year
            start_date = date(current_year, 1, 1)
            end_date = date(current_year, 12, 31)
            has_data_in_range = False
        else:
            start_date = min(all_dates)
            end_date = max(all_dates)
            has_data_in_range = True
    
    # Generate list of all months from start to end
    months_data = []
    current_month = start_date.replace(day=1)  # Start from first day of the month
    
    while current_month <= end_date:
        months_data.append({
            'year': current_month.year,
            'month': current_month.month,
            'label': current_month.strftime('%b %Y')
        })
        current_month += relativedelta(months=1)
    
    month_labels = [month_data['label'] for month_data in months_data]

    def monthly_sum(queryset, field, date_field, is_expense=False):
        sums = []
        for month_data in months_data:
            # Apply date range filter if custom dates are provided
            filtered_queryset = queryset
            if custom_start_date and custom_end_date:
                if is_expense:
                    # For expenses, filter using the already annotated date_dt field
                    filtered_queryset = queryset.filter(date_dt__range=[start_date, end_date])
                else:
                    filtered_queryset = queryset.filter(**{
                        f"{date_field}__range": [start_date, end_date]
                    })
            
            total = (
                filtered_queryset
                .annotate(month=ExtractMonth(date_field), year=ExtractYear(date_field))
                .filter(month=month_data['month'], year=month_data['year'])
                .aggregate(
                    total=Coalesce(Sum(field), Value(Decimal('0.00')), output_field=DecimalField())
                )['total']
            )
            sums.append(total)
        return sums

    # Generate monthly aggregates only if we have data or no custom range is specified
    if has_data_in_range or not (custom_start_date and custom_end_date):
        sales = monthly_sum(Order.objects, 'grand_total', 'date')
        services = monthly_sum(Invoice.objects, 'amount', 'created_at')
        purchase_returns = [Decimal('0.00')] * len(months_data)
        purchases = monthly_sum(Purchase.objects, 'grand_total', 'order_date')

        gross_profit = [s + srv + pr - p for s, srv, pr, p in zip(sales, services, purchase_returns, purchases)]

        # Expenses: cast textual date field to real DateField before extraction
        expenses_qs = Expense.objects.annotate(
            date_dt=Cast('date', DateField())
        )
        expenses = monthly_sum(expenses_qs, 'amount', 'date_dt', is_expense=True)

        sales_returns = [Decimal('0.00')] * len(months_data)
        total_expense = [p + exp + sr for p, exp, sr in zip(purchases, expenses, sales_returns)]
        net_profit = [gp - exp for gp, exp in zip(gross_profit, expenses)]
    else:
        # No data in selected range - create empty arrays
        empty_data = [Decimal('0.00')] * len(months_data)
        sales = empty_data[:]
        services = empty_data[:]
        purchase_returns = empty_data[:]
        purchases = empty_data[:]
        gross_profit = empty_data[:]
        expenses = empty_data[:]
        sales_returns = empty_data[:]
        total_expense = empty_data[:]
        net_profit = empty_data[:]

    # Generate filename suffix for exports
    filename_suffix = ""
    if custom_start_date and custom_end_date:
        filename_suffix = f"_{custom_start_date.strftime('%d-%m-%Y')}_to_{custom_end_date.strftime('%d-%m-%Y')}"

    context = {
        'month_labels': month_labels,
        'sales': sales,
        'services': services,
        'purchase_returns': purchase_returns,
        'purchases': purchases,
        'gross_profit': gross_profit,
        'expenses': expenses,
        'sales_returns': sales_returns,
        'total_expense': total_expense,
        'net_profit': net_profit,
        'date_range': date_range,
        'error_message': error_message,
        'has_data_in_range': has_data_in_range,
        'custom_date_range': bool(custom_start_date and custom_end_date),
    }

    # Handle exports
    exp = request.GET.get('export')
    if exp == 'excel':
        return export_profit_loss_excel(context, f'profit_loss_report{filename_suffix}')
    if exp == 'pdf':
        return export_profit_loss_pdf(context, f'profit_loss_report{filename_suffix}')

    # Build export URLs with current filters
    export_params = {}
    if date_range:
        export_params['date_range'] = date_range
    
    from urllib.parse import urlencode
    export_query_string = urlencode(export_params)
    export_excel_url = f'?export=excel&{export_query_string}' if export_query_string else '?export=excel'
    export_pdf_url = f'?export=pdf&{export_query_string}' if export_query_string else '?export=pdf'

    context.update({
        'export_excel_url': export_excel_url,
        'export_pdf_url': export_pdf_url,
    })

    return render(request, 'reports/profit-loss-report.html', context)
@login_required


def opening_inventory_report(request):
    """
    Opening Inventory Report showing opening inventory, units sold, and closing inventory
    for selected date range.
    """
    from datetime import datetime, timedelta
    from django.db.models import Sum, F, Q, Case, When, IntegerField
    from inventory.models import Stock
    
    # Parse date filters
    date_range = request.GET.get('date_range', '').strip()
    start_date = end_date = None
    error_message = None
    
    # Set default to today if no date range provided
    if not date_range:
        today = datetime.now().date()
        start_date = end_date = today
        date_range = f"{today.strftime('%d/%m/%Y')} - {today.strftime('%d/%m/%Y')}"
    else:
        try:
            start_str, end_str = date_range.split(' - ')
            start_str = start_str.strip()
            end_str = end_str.strip()
            
            # Try both formats: dd/mm/yyyy (from date picker) and dd-mm-yyyy (alternative)
            date_formats = ['%d/%m/%Y', '%d-%m-%Y']
            
            for date_format in date_formats:
                try:
                    start_date = datetime.strptime(start_str, date_format).date()
                    end_date = datetime.strptime(end_str, date_format).date()
                    break
                except ValueError:
                    continue
            
            if not start_date or not end_date:
                raise ValueError("Invalid date format")
            
            # Validate date range
            if start_date > end_date:
                error_message = "Start date must be before or equal to end date."
                start_date = end_date = None
                
        except (ValueError, AttributeError):
            error_message = "Invalid date format. Please use the date picker to select dates."
            start_date = end_date = None

    # Generate filename suffix for exports
    filename_suffix = ""
    if start_date and end_date:
        if start_date == end_date:
            filename_suffix = f"_{start_date.strftime('%d-%m-%Y')}"
        else:
            filename_suffix = f"_{start_date.strftime('%d-%m-%Y')}_to_{end_date.strftime('%d-%m-%Y')}"

    # Initialize report data
    report_rows = []
    
    if start_date and end_date:
        # Get all products with stock entries
        products_with_stock = Product.objects.select_related(
            'category', 'units'
        ).prefetch_related('stock_entries').filter(
            stock_entries__isnull=False
        ).distinct()

        for product in products_with_stock:
            stock_entry = product.stock_entries.first()
            if not stock_entry:
                continue
                
            # Current quantity (this represents closing inventory at end of period)
            current_qty = stock_entry.quantity
            
            # Calculate units sold during the period
            sold_qty = OrderItem.objects.filter(
                product=product,
                order__date__range=(start_date, end_date),
                order__status=Order.Status.COMPLETED
            ).aggregate(
                total_sold=Sum('quantity')
            )['total_sold'] or 0
            
            # Calculate opening inventory (current + sold during period)
            opening_qty = current_qty + sold_qty
            
            # Only include products that had activity (opening > 0 or sold > 0)
            if opening_qty > 0 or sold_qty > 0:
                report_rows.append({
                    'product_name': product.name,
                    'category': product.category.name if product.category else 'Uncategorized',
                    'unit': product.units.short_name if product.units else 'pcs',
                    'opening_qty': opening_qty,
                    'sold_qty': sold_qty,
                    'closing_qty': current_qty,
                    'sku': product.sku,
                })

        # Sort by product name
        report_rows.sort(key=lambda x: x['product_name'])

    # Handle exports
    exp = request.GET.get('export')
    if exp == 'excel':
        return export_opening_inventory_excel(report_rows, f'opening_inventory{filename_suffix}')
    if exp == 'pdf':
        return export_opening_inventory_pdf(report_rows, f'opening_inventory{filename_suffix}')

    # Build export URLs with current filters
    export_params = {}
    if date_range:
        export_params['date_range'] = date_range
    
    from urllib.parse import urlencode
    export_query_string = urlencode(export_params)
    export_excel_url = f'?export=excel&{export_query_string}' if export_query_string else '?export=excel'
    export_pdf_url = f'?export=pdf&{export_query_string}' if export_query_string else '?export=pdf'

    context = {
        'report_rows': report_rows,
        'date_range': date_range,
        'start_date': start_date,
        'end_date': end_date,
        'error_message': error_message,
        'export_excel_url': export_excel_url,
        'export_pdf_url': export_pdf_url,
        'total_products': len(report_rows),
        'total_opening_qty': sum(row['opening_qty'] for row in report_rows),
        'total_sold_qty': sum(row['sold_qty'] for row in report_rows),
        'total_closing_qty': sum(row['closing_qty'] for row in report_rows),
    }

    return render(request, 'reports/opening-inventory-report.html', context)