from django.shortcuts import render
from django.shortcuts import render
from django.db.models import Sum, Count, F, Value,DecimalField,ExpressionWrapper
from django.db.models.functions import Coalesce
from django.utils import timezone
from datetime import timedelta, date
from people.models import *
from decimal import Decimal
from django.core.paginator import Paginator
import json
from django.db.models import Q
from calendar import monthrange

from inventory.models import Product,Stock
from purchases.models import Purchase
from sales.models import Order, OrderItem
from finance.models import Expense,ExpenseCategory
from sales.models import Invoice
from .forms import DateRangeFilterForm
from django.contrib.auth.decorators import login_required


def get_date_range(date_range, start_date, end_date):
    """Helper function to calculate date range based on selection"""
    today = timezone.now().date()
    
    if date_range == 'today':
        return today, today
    elif date_range == 'yesterday':
        yesterday = today - timedelta(days=1)
        return yesterday, yesterday
    elif date_range == 'last_7_days':
        start_date = today - timedelta(days=6)  # Fixed: should be 6 days ago to include today
        return start_date, today
    elif date_range == 'last_30_days':
        start_date = today - timedelta(days=29)  # Fixed: should be 29 days ago to include today
        return start_date, today
    elif date_range == 'this_month':
        return today.replace(day=1), today
    elif date_range == 'last_month':
        first_day_this_month = today.replace(day=1)
        last_day_last_month = first_day_this_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        return first_day_last_month, last_day_last_month
    elif date_range == 'custom' and start_date and end_date:
        return start_date, end_date
    else:
        # Default to all time (no filtering)
        return None, None


def format_percentage(value):
    """Helper function to format percentage to 2 decimal places"""
    if value is None:
        return "0.00"
    return f"{value:.2f}"


# Create your views here.
def homepage(request):
    # Handle date range filtering
    form = DateRangeFilterForm(request.GET or None)
    filter_start_date = None
    filter_end_date = None
    date_range_error = None
    
    if form.is_valid():
        date_range = form.cleaned_data.get('date_range')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        
        filter_start_date, filter_end_date = get_date_range(date_range, start_date, end_date)
    elif form.errors:
        date_range_error = "Please select a valid date range."

    today = timezone.now().date()
    last_30 = today - timedelta(days=30)
    prev_30 = last_30 - timedelta(days=30)

    # Apply date filtering to queries
    def apply_date_filter(queryset, date_field):
        if filter_start_date and filter_end_date:
            filter_kwargs = {
                f"{date_field}__gte": filter_start_date,
                f"{date_field}__lte": filter_end_date
            }
            return queryset.filter(**filter_kwargs)
        return queryset

    # Total Sales and % change
    total_sales_qs = Order.objects.filter(status=Order.Status.COMPLETED)
    total_sales_qs = apply_date_filter(total_sales_qs, 'date')
    total_sales = total_sales_qs.aggregate(
        total=Coalesce(Sum('grand_total', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    )['total']
    
    sales_last_30 = Order.objects.filter(
        status=Order.Status.COMPLETED,
        date__gte=last_30
    ).aggregate(
        total=Coalesce(Sum('grand_total', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    )['total']
    sales_prev_30 = Order.objects.filter(
        status=Order.Status.COMPLETED,
        date__range=(prev_30, last_30)
    ).aggregate(
        total=Coalesce(Sum('grand_total', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    )['total']
    sales_change = ((sales_last_30 - sales_prev_30) / sales_prev_30 * 100) if sales_prev_30 else 0

    # Cash at Hand = sales - purchases - expenses (previously called profit)
    cogs_qs = Purchase.objects.filter(status=Purchase.Status.RECEIVED)
    cogs_qs = apply_date_filter(cogs_qs, 'order_date')
    cogs_current = cogs_qs.aggregate(
        total=Coalesce(Sum('grand_total', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    )['total']
    
    exp_qs = Expense.objects.all()
    exp_qs = apply_date_filter(exp_qs, 'date_created__date')
    exp_current = exp_qs.aggregate(
        total=Coalesce(Sum('amount', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    )['total']
    
    # Calculate invoice due amount for current period
    invoice_due_qs = Invoice.objects.all()
    invoice_due_qs = apply_date_filter(invoice_due_qs, 'due_date')
    invoice_due_current = invoice_due_qs.aggregate(
        total=Coalesce(Sum('amount_due', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    )['total']
    
    # Cash at hand = sales - purchases - expenses - invoice due
    cash_at_hand = total_sales - cogs_current - exp_current - invoice_due_current
    
    # cash at hand change vs previous period - calculate comparison period based on filter
    if filter_start_date and filter_end_date:
        # Calculate the same period length but in the past for comparison
        period_length = (filter_end_date - filter_start_date).days + 1
        comparison_end = filter_start_date - timedelta(days=1)
        comparison_start = comparison_end - timedelta(days=period_length - 1)
        
        # Sales comparison
        sales_comparison = Order.objects.filter(
            status=Order.Status.COMPLETED,
            date__gte=comparison_start,
            date__lte=comparison_end
        ).aggregate(
            total=Coalesce(Sum('grand_total', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
        
        # COGS comparison
        cogs_comparison = Purchase.objects.filter(
            status=Purchase.Status.RECEIVED,
            order_date__gte=comparison_start,
            order_date__lte=comparison_end
        ).aggregate(
            total=Coalesce(Sum('grand_total', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
        
        # Expenses comparison
        exp_comparison = Expense.objects.filter(
            date_created__date__gte=comparison_start,
            date_created__date__lte=comparison_end
        ).aggregate(
            total=Coalesce(Sum('amount', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
        
        # Invoice due comparison
        invoice_due_comparison = Invoice.objects.filter(
            due_date__gte=comparison_start,
            due_date__lte=comparison_end
        ).aggregate(
            total=Coalesce(Sum('amount_due', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
        
        cash_at_hand_prev = sales_comparison - cogs_comparison - exp_comparison - invoice_due_comparison
    else:
        # Default to last 30 days comparison
        cogs_prev_30 = Purchase.objects.filter(
            status=Purchase.Status.RECEIVED,
            order_date__range=(prev_30, last_30)
        ).aggregate(
            total=Coalesce(Sum('grand_total', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
        exp_prev_30 = Expense.objects.filter(
            date_created__date__range=(prev_30, last_30)
        ).aggregate(
            total=Coalesce(Sum('amount', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
        invoice_due_prev_30 = Invoice.objects.filter(
            due_date__range=(prev_30, last_30)
        ).aggregate(
            total=Coalesce(Sum('amount_due', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
        cash_at_hand_prev = sales_prev_30 - cogs_prev_30 - exp_prev_30 - invoice_due_prev_30
    
    cash_at_hand_change = ((cash_at_hand - cash_at_hand_prev) / cash_at_hand_prev * 100) if cash_at_hand_prev else 0

    # Product Profit = (sale_price - purchase_price) for sold items
    # Calculate product profit with date filtering
    product_profit_qs = OrderItem.objects.filter(order__status=Order.Status.COMPLETED)
    product_profit_qs = apply_date_filter(product_profit_qs, 'order__date').select_related('product')
    
    # Calculate product profit by summing (unit_cost - product.purchase_price) * quantity for each order item
    product_profit = Decimal('0.00')
    for item in product_profit_qs:
        profit_per_unit = item.unit_cost - item.product.purchase_price
        product_profit += profit_per_unit * item.quantity
    
    # Product profit comparison period
    if filter_start_date and filter_end_date:
        # Calculate the same period length but in the past for comparison (matching cash at hand logic)
        period_length = (filter_end_date - filter_start_date).days + 1
        comparison_end = filter_start_date - timedelta(days=1)
        comparison_start = comparison_end - timedelta(days=period_length - 1)
        
        product_profit_prev_qs = OrderItem.objects.filter(
            order__status=Order.Status.COMPLETED,
            order__date__gte=comparison_start,
            order__date__lte=comparison_end
        ).select_related('product')
    else:
        # Default to previous 30 days
        product_profit_prev_qs = OrderItem.objects.filter(
            order__status=Order.Status.COMPLETED,
            order__date__gte=prev_30,
            order__date__lt=last_30
        ).select_related('product')
    
    product_profit_prev = Decimal('0.00')
    for item in product_profit_prev_qs:
        profit_per_unit = item.unit_cost - item.product.purchase_price
        product_profit_prev += profit_per_unit * item.quantity
    
    product_profit_change = ((product_profit - product_profit_prev) / product_profit_prev * 100) if product_profit_prev else 0

    # Invoice Due and % change - calculate comparison period
    if filter_start_date and filter_end_date:
        # Calculate the same period length but in the past for comparison
        period_length = (filter_end_date - filter_start_date).days + 1
        comparison_end = filter_start_date - timedelta(days=1)
        comparison_start = comparison_end - timedelta(days=period_length - 1)
        
        invoice_due_prev = Invoice.objects.filter(
            due_date__gte=comparison_start,
            due_date__lte=comparison_end
        ).aggregate(
            total=Coalesce(Sum('amount_due', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
    else:
        # Default to last 30 days comparison
        invoice_due_prev = Invoice.objects.filter(
            due_date__range=(prev_30, last_30)
        ).aggregate(
            total=Coalesce(Sum('amount_due', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
    
    invoice_due_change = ((invoice_due_current - invoice_due_prev) / invoice_due_prev * 100) if invoice_due_prev else 0

    # Total Expenses and % change
    total_expenses = exp_current
    
    # Calculate expenses change based on the same logic as cash at hand
    if filter_start_date and filter_end_date:
        # Calculate the same period length but in the past for comparison (matching cash at hand logic)
        period_length = (filter_end_date - filter_start_date).days + 1
        comp_end = filter_start_date - timedelta(days=1)
        comp_start = comp_end - timedelta(days=period_length - 1)
        
        expenses_prev = Expense.objects.filter(
            date_created__date__gte=comp_start,
            date_created__date__lte=comp_end
        ).aggregate(
            total=Coalesce(Sum('amount', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
    else:
        # Default to last 30 days comparison
        expenses_last_30 = Expense.objects.filter(date_created__date__gte=last_30).aggregate(
            total=Coalesce(Sum('amount', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
        expenses_prev_30 = Expense.objects.filter(
            date_created__date__range=(prev_30, last_30)
        ).aggregate(
            total=Coalesce(Sum('amount', output_field=DecimalField()), Value(0, output_field=DecimalField()))
        )['total']
        expenses_prev = expenses_prev_30
    
    expenses_change = ((total_expenses - expenses_prev) / expenses_prev * 100) if expenses_prev else 0

    # Chart Data - Sales and Purchases by day/period
    chart_data = get_chart_data(filter_start_date, filter_end_date)

    top_products = (
        Product.objects
        .filter(order_items__order__status='completed')
        .annotate(total_quantity_sold=Sum('order_items__quantity'))
        .order_by('-total_quantity_sold')[:7]
    )

    low_stocks = (
        Stock.objects
             .select_related(
                 'product',
                 'product__category',
                 'product__sub_category',
                 'product__units',
             )
             .filter(quantity__lt=F('quantity_alert'))
             .order_by('product__name')
    )
    low_stocks = Paginator(low_stocks,10)
    low_stocks = low_stocks.page(1)

    recent_sales = Paginator(OrderItem.objects.order_by('-id').all(),7)
    recent_sales = recent_sales.page(1)

    # Calculate total purchases with date filtering
    total_purchases_qs = Purchase.objects.select_related('supplier').prefetch_related('items__product').order_by('-order_date', 'reference')
    total_purchases_qs = apply_date_filter(total_purchases_qs, 'order_date')
    total_purchases = total_purchases_qs.aggregate(
        total=Coalesce(
            Sum('grand_total'),
            Value(Decimal('0.00'), output_field=DecimalField()),
            output_field=DecimalField()
        )
    )['total']

    # Remove payment returns as it's now product profit (calculated above)
    
    context = {
        'form': form,
        'date_range_error': date_range_error,
        'filter_start_date': filter_start_date,
        'filter_end_date': filter_end_date,
        'total_sales': total_sales,
        'sales_change': format_percentage(sales_change),
        'cash_at_hand': cash_at_hand,
        'cash_at_hand_change': format_percentage(cash_at_hand_change),
        'product_profit': product_profit,
        'product_profit_change': format_percentage(product_profit_change),
        'invoice_due_last_30': invoice_due_current,
        'invoice_due_change': format_percentage(invoice_due_change),
        'total_expenses': total_expenses,
        'expenses_change': format_percentage(expenses_change),
        'suppliers': Supplier.objects.count(),
        'customers': Customer.objects.count(),
        'orders': Order.objects.count(),
        'purchases': Purchase.objects.count(),
        'best_sellers': top_products,
        'low_stocks': low_stocks,
        'recent_sales': recent_sales,
        'total_purchases': total_purchases,
        'chart_data': json.dumps(chart_data),
    }
    
    return render(request, 'landing/homepage.html', context)


def get_chart_data(start_date, end_date):
    """Generate chart data for sales and purchases"""
    if not start_date or not end_date:
        # Default to last 30 days if no filter
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=29)
    
    # Calculate the number of days
    days_diff = (end_date - start_date).days + 1
    
    # Generate date range
    dates = []
    labels = []
    timestamps = []
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(current_date)
        timestamps.append(current_date.strftime('%Y-%m-%d'))
        if days_diff <= 7:
            # Show full date for week or less
            labels.append(current_date.strftime('%m/%d'))
        elif days_diff <= 31:
            # Show day for month or less
            labels.append(current_date.strftime('%d'))
        else:
            # Show month/day for longer periods
            labels.append(current_date.strftime('%m/%d'))
        current_date += timedelta(days=1)
    
    # Get sales data
    sales_data = []
    for date in dates:
        daily_sales = Order.objects.filter(
            date=date,
            status=Order.Status.COMPLETED
        ).aggregate(
            total=Coalesce(Sum('grand_total'), Value(0, output_field=DecimalField()))
        )['total']
        sales_data.append(float(daily_sales) if daily_sales else 0)
    
    # Get purchase data
    purchase_data = []
    for date in dates:
        daily_purchases = Purchase.objects.filter(
            order_date=date,
            status=Purchase.Status.RECEIVED
        ).aggregate(
            total=Coalesce(Sum('grand_total'), Value(0, output_field=DecimalField()))
        )['total']
        purchase_data.append(float(daily_purchases) if daily_purchases else 0)
    
    return {
        'labels': labels,
        'sales_data': sales_data,
        'purchase_data': purchase_data,
        'timestamps': timestamps
    }
@login_required


def sales_dashboard(request):
    # Date ranges
    today = timezone.now().date()
    start_week = today - timedelta(days=7)
    prev_start = start_week - timedelta(days=7)
    prev_end = start_week

    # Weekly earnings
    week_sum = Order.objects.filter(
        date__gte=start_week, date__lt=today, status=Order.Status.COMPLETED
    ).aggregate(
        total=Coalesce(Sum('grand_total', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    )['total']
    prev_week_sum = Order.objects.filter(
        date__gte=prev_start, date__lt=prev_end, status=Order.Status.COMPLETED
    ).aggregate(
        total=Coalesce(Sum('grand_total', output_field=DecimalField()), Value(0, output_field=DecimalField()))
    )['total']
    # Percentage change
    if prev_week_sum > 0:
        week_change = (week_sum - prev_week_sum) / prev_week_sum * 100
    else:
        week_change = 0

    # Totals
    total_sales_count = Order.objects.filter(status=Order.Status.COMPLETED).count()
    total_purchases_count = Purchase.objects.filter(status=Purchase.Status.RECEIVED).count()

    # Best sellers (top 5 by quantity)
    total_revenue_expr = ExpressionWrapper(
        F('quantity') * F('unit_cost'), output_field=DecimalField()
    )
    best_sellers_qs = (
        OrderItem.objects
        .filter(order__status=Order.Status.COMPLETED)
        .values(
            'product__id',
            'product__name',
        )
        .annotate(
            total_qty=Coalesce(Sum('quantity', output_field=DecimalField()), Value(0, output_field=DecimalField())),
            total_revenue=Coalesce(Sum(total_revenue_expr), Value(0, output_field=DecimalField()))
        )
        .order_by('-total_qty')[:5]
    )
    best_sellers = list(best_sellers_qs)

    # Recent transactions (last 5 orders)
    recent_orders_qs = (
        Order.objects
        .select_related('customer')
        .order_by('-date')[:5]
    )
    recent_transactions = []
    for o in recent_orders_qs:
        first_item = o.items.first()
        minutes = None
        if isinstance(o.date, date):
            diff = timezone.now().date() - o.date
            minutes = diff.days * 24 * 60
        recent_transactions.append({
            'id': o.pk,
            'product_name': first_item.product.name if first_item else '',
            'product_image': first_item.product.first_image_url if first_item else '',
            'time_since': minutes,
            'payment_method': o.source,
            'reference': o.reference,
            'status': o.payment_status,
            'amount': o.grand_total,
        })

    # Sales analytics: monthly sales for current year
    current_year = today.year
    months = list(range(1, 13))
    month_labels = [date(current_year, m, 1).strftime('%b') for m in months]
    monthly_sales = []
    for m in months:
        total = (
            Order.objects
            .filter(date__year=current_year, date__month=m, status=Order.Status.COMPLETED)
            .aggregate(
                total=Coalesce(Sum('grand_total', output_field=DecimalField()), Value(0, output_field=DecimalField()))
            )['total']
        )
        monthly_sales.append(total)

    # Sales by country
    country_sales_qs = (
        Order.objects
        .filter(status=Order.Status.COMPLETED)
        .values('customer__country')
        .annotate(total=Coalesce(Sum('grand_total', output_field=DecimalField()), Value(0, output_field=DecimalField())))
    )
    country_sales = list(country_sales_qs)

    context = {
        'weekly_earning': week_sum,
        'week_change': format_percentage(week_change),
        'total_sales_count': total_sales_count,
        'total_purchases_count': total_purchases_count,
        'best_sellers': best_sellers,
        'recent_transactions': recent_transactions,
        'month_labels': month_labels,
        'monthly_sales': monthly_sales,
        'country_sales': country_sales,
    }
    return render(request, 'landing/sales-dashboard.html', context)