from django.shortcuts import render,get_object_or_404
from inventory.models import Category,Product
from people.models import Customer
from sales.services.order_service import OrderManager
from django.db.models import Prefetch
from .models import Order, OrderItem
from django.db.models import F
from django.http import JsonResponse
from decimal import Decimal
from .utils import *
from django.utils import timezone
from django.db.models import Sum, Q
from finance.models import Expense
from purchases.models import Purchase, PurchaseItem
from inventory.models import Stock
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta

@login_required

# Create your views here.
def online_orders(request):
    search = request.GET.get('search', '').strip()
    export = request.GET.get('export', '').lower()

    qs = get_orders_queryset(search=search, source='online')
    if export == 'excel':
        return export_orders_excel(qs, basename='online-orders')
    if export == 'pdf':
        return export_orders_pdf(qs, basename='online-orders')

    return render(request, 'sales/online-orders.html', {
        'orders': qs,
        'search': search,
        'export_excel_url': f'?export=excel&search={search}',
        'export_pdf_url':   f'?export=pdf&search={search}',
    })
@login_required


def pos_orders(request):
    search = request.GET.get('search', '').strip()
    export = request.GET.get('export', '').lower()
    
    # Get filter parameters
    customer = request.GET.get('customer', '').strip()
    status = request.GET.get('status', '').strip()  # Single selection
    payment_status = request.GET.get('payment_status', '').strip()  # Single selection
    sort_by = request.GET.get('sort_by', '').strip()

    qs = get_orders_queryset(
        search=search, 
        source='pos',
        customer=customer,
        status=status,
        payment_status=payment_status,
        sort_by=sort_by
    )
    
    if export == 'excel':
        return export_orders_excel(qs, basename='pos-orders')
    if export == 'pdf':
        return export_orders_pdf(qs, basename='pos-orders')

    # Get filter options for dropdowns
    customers = Customer.objects.all().order_by('name')
    statuses = Order.Status.choices
    payment_statuses = Order.PaymentStatus.choices

    return render(request, 'sales/pos-orders.html', {
        'orders': qs,
        'search': search,
        'customers': customers,
        'statuses': statuses,
        'payment_statuses': payment_statuses,
        'selected_customer': customer,
        'selected_status': status,
        'selected_payment_status': payment_status,
        'selected_sort': sort_by,
        'export_excel_url': f'?export=excel&search={search}',
        'export_pdf_url':   f'?export=pdf&search={search}',
    })
@login_required


@csrf_exempt
def update_payment(request, order_id):
    """
    Handle partial payment updates via AJAX
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    try:
        order = get_object_or_404(Order, pk=order_id)
        
        # Parse request data
        data = json.loads(request.body)
        additional_amount = Decimal(str(data.get('amount', '0')))
        payment_type = data.get('payment_type', 'cash')
        
        # Validate amount
        if additional_amount <= 0:
            return JsonResponse({
                'success': False, 
                'error': 'Amount must be greater than zero'
            })
        
        # Check for overpayment
        remaining_due = order.grand_total - order.paid_amount
        if additional_amount > remaining_due:
            return JsonResponse({
                'success': False, 
                'error': f'Amount exceeds due amount. Maximum allowed: KES {remaining_due}'
            })
        
        # Update payment
        order.paid_amount += additional_amount
        order.update_totals()  # This will recalculate payment_status
        
        # Return updated order data
        return JsonResponse({
            'success': True,
            'order': {
                'id': order.pk,
                'paid_amount': str(order.paid_amount),
                'due_amount': str(order.due_amount),
                'payment_status': order.payment_status,
                'payment_status_display': order.get_payment_status_display(),
            }
        })
        
    except (ValueError, TypeError) as e:
        return JsonResponse({
            'success': False, 
            'error': 'Invalid amount provided'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'An error occurred: {str(e)}'
        })
@login_required


def get_customers_ajax(request):
    """
    AJAX endpoint to get customers for dropdown population
    """
    search = request.GET.get('q', '').strip()
    customers = Customer.objects.all()
    
    if search:
        customers = customers.filter(name__icontains=search)
    
    customers = customers.order_by('name')[:50]  # Limit to 50 results
    
    data = {
        'customers': [
            {
                'id': customer.id,
                'name': customer.name,
                'email': customer.email
            }
            for customer in customers
        ]
    }
    
    return JsonResponse(data)
@login_required


def sales_return(request):
    return render(request,'sales/sales-returns.html',{})
@login_required

def pos(request):
    categories = Category.objects.prefetch_related(
        'products__stock_entries',  
        'products__images'          
    )

    all_products = Product.objects.select_related(
        'category',
        'sub_category',
        'units'
    ).prefetch_related(
        'stock_entries', 
        'images'          
    )
    return render(request,'sales/pos.html',{
        'categories':categories,
        'customers':Customer.objects.all(),
        'all_products':  all_products

    })
@login_required

def create_order(request):
    if request.method == 'POST':
        return OrderManager.create_order(request)
    else:
        return JsonResponse({"success": False, "error": "Method not allowed"}, status=405)
@login_required

def order_detail_json(request, pk):
    order = get_object_or_404(
        Order.objects
             .select_related('customer', 'biller')
             .prefetch_related('items__product'),
        pk=pk
    )

    # Serialize items
    items = []
    for itm in order.items.all():
        items.append({
            'product_name'   : itm.product.name,
            'purchase_price' : str(itm.purchase_price),
            'discount'       : str(itm.discount),
            'tax'            : str(itm.tax),
            'tax_amount'     : str(itm.tax_amount),
            'unit_cost'      : str(itm.unit_cost),
            'quantity'       : itm.quantity,
            'total_cost'     : str(itm.total_cost),
        })

        
    data = {
        'customer': {
            'name'    : order.customer.name if order.customer else 'walk in customer',
            'image'   : order.customer.image.url if order.customer else 'https://imgs.search.brave.com/9a-iE4YQlxsHtJE0iTvKmrY3joy4A1vKGPfnVyYr-NE/rs:fit:860:0:0:0/g:ce/aHR0cHM6Ly9tZWRp/YS5pc3RvY2twaG90/by5jb20vaWQvMTIx/NDQyODMwMC92ZWN0/b3IvZGVmYXVsdC1w/cm9maWxlLXBpY3R1/cmUtYXZhdGFyLXBo/b3RvLXBsYWNlaG9s/ZGVyLXZlY3Rvci1p/bGx1c3RyYXRpb24u/anBnP3M9NjEyeDYx/MiZ3PTAmaz0yMCZj/PXZmdE1kTGhsZER4/OWhvdU40Vi1nM0M5/azB4bDZZZUJjb0Jf/Ums2VHJjZTA9',
            'address' : getattr(order.customer, 'address', '') if order.customer else 'N/A',
            'email'   : order.customer.email if order.customer else 'N/A',
            'phone'   : order.customer.phone if order.customer else 'N/A',
        },
        'invoice': {
            'reference'      : order.reference,
            'date'           : order.date.strftime('%b %d, %Y'),
            'status'         : order.status,
            'payment_status' : order.payment_status,
            'biller'         : str(order.biller),
        },
        'items' : items,
        'totals': {
            'order_tax'  : str(order.grand_total - sum(Decimal(i['total_cost']) for i in items)),
            'discount'   : '0.00',  # if you track order-level discount, fill here
            'grand_total': str(order.grand_total),
            'paid'       : str(order.paid_amount),
            'due'        : str(order.due_amount),
        },
        'payment_details': {
            'payment_type': 'cash',  # Default to cash for POS orders
            'received_amount': str(order.paid_amount),
            'payment_status': order.payment_status,
            'created_at': order.date.strftime('%Y-%m-%d %H:%M:%S') if hasattr(order, 'created_at') else order.date.strftime('%Y-%m-%d'),
            'change_amount': str(max(order.paid_amount - order.grand_total, Decimal('0.00'))),
            'total_amount': str(order.grand_total),
            'due_amount': str(order.due_amount),
        }
    }
    return JsonResponse(data)
@login_required

def cash_register_data(request):
    """
    Endpoint to fetch cash register metrics
    """
    try:
        today = timezone.now().date()
        
        # Get today's completed orders
        today_orders = Order.objects.filter(
            date=today,
            status=Order.Status.COMPLETED
        )
        
        # Calculate cash in hand (assuming this is the total cash payments received)
        cash_payments = today_orders.filter(
            payment_status__in=[Order.PaymentStatus.PAID, Order.PaymentStatus.OVERPAID]
        ).aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
        
        # Total sale amount (all completed orders today)
        total_sale = today_orders.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
        
        # Total payment (all payments received today)
        total_payment = today_orders.aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
        
        # Cash payment (orders paid with cash - assuming we track this in source or payment details)
        cash_payment = today_orders.filter(
            payment_status__in=[Order.PaymentStatus.PAID, Order.PaymentStatus.OVERPAID]
        ).aggregate(total=Sum('paid_amount'))['total'] or Decimal('0.00')
        
        # Total sale returns (assuming negative grand_total or separate return tracking)
        # For now, we'll calculate this as orders with negative amounts or a separate return system
        total_returns = Decimal('0.00')  # Placeholder - implement based on your return system
        
        # Total expenses for today
        total_expenses = Expense.objects.filter(
            date=today.strftime('%Y-%m-%d')  # Expense model uses TextField for date
        ).aggregate(
            total=Sum('amount')  # Convert text to decimal if needed
        )['total'] or Decimal('0.00')
        
        # Handle text field conversion for expenses
        if isinstance(total_expenses, str):
            try:
                total_expenses = Decimal(total_expenses)
            except:
                total_expenses = Decimal('0.00')
        
        # Total cash calculation
        total_cash = cash_payments - total_returns - total_expenses
        
        # Format currency for KES
        def format_kes(amount):
            return f"KES {amount:,.2f}"
        
        data = {
            'success': True,
            'data': {
                'cash_in_hand': format_kes(cash_payments),
                'total_sale_amount': format_kes(total_sale),
                'total_payment': format_kes(total_payment),
                'cash_payment': format_kes(cash_payment),
                'total_sale_return': format_kes(total_returns),
                'total_expense': format_kes(total_expenses),
                'total_cash': format_kes(total_cash)
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
@login_required

def today_profit_data(request):
    """
    Endpoint to fetch today's profit data
    """
    try:
        today = timezone.now().date()
        
        # Get today's completed orders
        today_orders = Order.objects.filter(
            date=today,
            status=Order.Status.COMPLETED
        )
        
        # Calculate total sales (revenue)
        total_sales = today_orders.aggregate(total=Sum('grand_total'))['total'] or Decimal('0.00')
        
        # Calculate total cost of goods sold
        total_cost = Decimal('0.00')
        for order in today_orders.prefetch_related('items__product'):
            for item in order.items.all():
                # Get the cost price from purchase data or use a default cost calculation
                try:
                    # Try to get the latest purchase cost for this product
                    latest_purchase = PurchaseItem.objects.filter(
                        product=item.product
                    ).order_by('-purchase__order_date').first()
                    
                    if latest_purchase:
                        cost_per_unit = latest_purchase.unit_cost
                    else:
                        # Fallback to 70% of selling price as cost (adjust as needed)
                        cost_per_unit = item.unit_cost * Decimal('0.7')
                    
                    total_cost += cost_per_unit * item.quantity
                except:
                    # Fallback calculation
                    total_cost += item.unit_cost * item.quantity * Decimal('0.7')
        
        # Get today's expenses
        today_expenses = Expense.objects.filter(
            date=today.strftime('%Y-%m-%d')
        )
        
        total_expenses = Decimal('0.00')
        for expense in today_expenses:
            try:
                expense_amount = Decimal(expense.amount)
                total_expenses += expense_amount
            except:
                continue
        
        # Calculate profit
        gross_profit = total_sales - total_cost
        net_profit = gross_profit - total_expenses
        
        # Format currency with K suffix for large amounts
        def format_kes_with_k(amount):
            if amount >= 1000:
                return f"KES {amount/1000:.1f}K"
            else:
                return f"KES {amount:.2f}"
        
        def format_kes(amount):
            return f"KES {amount:,.2f}"
        
        # Additional metrics for the detailed table
        product_revenue = total_sales
        product_cost = total_cost
        stock_adjustment = Decimal('0.00')  # Placeholder
        deposit_payment = Decimal('0.00')  # Placeholder
        purchase_shipping = Decimal('0.00')  # Placeholder
        sell_discount = Decimal('0.00')  # Placeholder
        sell_return = Decimal('0.00')  # Placeholder
        closing_stock = Decimal('0.00')  # Placeholder - calculate from inventory
        
        data = {
            'success': True,
            'data': {
                # Summary cards
                'total_sale': format_kes_with_k(total_sales),
                'expense': format_kes_with_k(total_expenses),
                'total_profit': format_kes_with_k(net_profit),
                
                # Detailed table
                'product_revenue': format_kes(product_revenue),
                'product_cost': format_kes(product_cost),
                'expense_detail': format_kes(total_expenses),
                'stock_adjustment': format_kes(stock_adjustment),
                'deposit_payment': format_kes(deposit_payment),
                'purchase_shipping': format_kes(purchase_shipping),
                'sell_discount': format_kes(sell_discount),
                'sell_return': format_kes(sell_return),
                'closing_stock': format_kes(closing_stock),
                'total_sales_detail': format_kes(total_sales),
                'total_sale_return': format_kes(sell_return),
                'total_expense_detail': format_kes(total_expenses),
                'total_cash': format_kes(net_profit)
            }
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def cashier_weekly_summary(request):
    """
    Endpoint to fetch weekly summary for cashier dashboard
    """
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    
    # Weekly metrics
    weekly_orders = Order.objects.filter(
        date__range=[week_start, week_end]
    )
    
    total_sales = weekly_orders.filter(status=Order.Status.COMPLETED).aggregate(
        total=Sum('grand_total')
    )['total'] or Decimal('0.00')
    
    total_orders = weekly_orders.count()
    
    # Generate daily breakdown
    daily_data = []
    current_date = week_start
    while current_date <= week_end:
        day_orders = weekly_orders.filter(date=current_date)
        day_sales = day_orders.filter(status=Order.Status.COMPLETED).aggregate(
            total=Sum('grand_total')
        )['total'] or Decimal('0.00')
        
        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'day': current_date.strftime('%A'),
            'sales': format_kes(day_sales),
            'orders': day_orders.count(),
        })
        current_date += timedelta(days=1)
    
    data = {
        'week_start': week_start.strftime('%b %d, %Y'),
        'week_end': week_end.strftime('%b %d, %Y'),
        'total_sales': format_kes(total_sales),
        'total_orders': total_orders,
        'daily_breakdown': daily_data,
    }
    
    return JsonResponse(data)


@login_required
@require_http_methods(["POST"])
def initiate_mpesa_payment(request):
    """
    Initiate M-Pesa STK Push payment
    """
    from .mpesa_service import MpesaService
    from .models import MpesaTransaction
    
    try:
        data = json.loads(request.body)
        
        # Extract payment details
        phone_number = data.get('phone_number', '').strip()
        amount = Decimal(str(data.get('amount', '0')))
        order_id = data.get('order_id')
        
        # Validate inputs
        if not phone_number:
            return JsonResponse({'success': False, 'message': 'Phone number is required'})
        
        if amount <= 0:
            return JsonResponse({'success': False, 'message': 'Invalid amount'})
        
        if not order_id:
            return JsonResponse({'success': False, 'message': 'Order ID is required'})
        
        # Get the order
        try:
            order = Order.objects.get(id=order_id)
        except Order.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Order not found'})
        
        # Prepare transaction details
        account_reference = f"ORDER-{order.reference}"
        transaction_desc = f"Payment for Order {order.reference}"
        
        # Initialize M-Pesa service
        mpesa_service = MpesaService()
        
        # Initiate STK Push (callback URL will be auto-generated via ngrok)
        result = mpesa_service.initiate_stk_push(
            phone_number=phone_number,
            amount=amount,
            account_reference=account_reference,
            transaction_desc=transaction_desc
        )
        
        if result['success']:
            # Update the transaction with order reference
            try:
                transaction = MpesaTransaction.objects.get(id=result['transaction_id'])
                transaction.order = order
                transaction.save()
            except MpesaTransaction.DoesNotExist:
                pass
            
            return JsonResponse({
                'success': True,
                'message': result['message'],
                'checkout_request_id': result['checkout_request_id']
            })
        else:
            # Enhanced error handling for specific ngrok issues and network failures
            error_message = result.get('message', 'Payment failed')
            error_code = result.get('error_code', '')
            reason = result.get('reason')
            
            status = 400
            if reason == 'network' or error_code in ('NETWORK_OFFLINE', 'SYSTEM_OFFLINE'):
                error_message = 'Payment request failed — system appears offline. Check your internet connection and try again.'
                status = 503
            elif 'ERR_NGROK_108' in str(result) or 'session limit' in error_message.lower():
                error_message = 'M-Pesa temporarily unavailable due to system session limits. Please try again in a few minutes.'
                status = 503
            
            return JsonResponse({
                'success': False,
                'message': error_message,
                'error_code': error_code,
                'reason': reason
            }, status=status)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except ValueError as e:
        return JsonResponse({'success': False, 'message': f'Invalid amount: {str(e)}'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})

from django.db import transaction

@csrf_exempt
@require_http_methods(["POST"])
def mpesa_callback(request):
    """
    Handle M-Pesa payment callback
    """
    from .mpesa_service import MpesaService
    
    try:
        callback_data = json.loads(request.body)
        
        # Initialize M-Pesa service
        mpesa_service = MpesaService()
        
        # Process the callback
        success = mpesa_service.handle_callback(callback_data)
        
        if success:
            return JsonResponse({'ResultCode': 0, 'ResultDesc': 'Success'})
        else:
            return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Failed'})
            
    except json.JSONDecodeError:
        return JsonResponse({'ResultCode': 1, 'ResultDesc': 'Invalid JSON'})

@login_required
@require_http_methods(["GET"])
def mpesa_system_status(request):
    """
    Check M-Pesa system status - now uses base URL instead of ngrok
    """
    from django.conf import settings
    
    try:
        # Since M-Pesa now uses base URL instead of ngrok, always return available
        base_url = getattr(settings, 'BASE_URL', 'https://your-domain.com')
        
        status = {
            'available': True,
            'status': 'online',
            'message': 'M-Pesa payments are available',
            'callback_url': f"{base_url}/dashboard/sales/mpesa-callback/"
        }
        
        return JsonResponse(status)
        
    except Exception as e:
        return JsonResponse({
            'available': True,  # Still return available even on error since we're not dependent on ngrok
            'status': 'online',
            'message': 'M-Pesa payments are available',
            'callback_url': f"{getattr(settings, 'BASE_URL', 'https://your-domain.com')}/dashboard/sales/mpesa-callback/"
        })


@login_required
@require_http_methods(["GET"])
def check_mpesa_status(request, checkout_request_id):
    """
    Check M-Pesa transaction status and mark timed-out transactions as failed
    """
    from .mpesa_service import MpesaService
    
    # First, check for and mark any timed-out transactions as failed
    mpesa_service = MpesaService()
    mpesa_service.mark_timeout_transactions_as_failed(timeout_minutes=5)
    
    try:
        result = mpesa_service.check_transaction_status(checkout_request_id)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
def mpesa_transactions(request):
    """
    View M-Pesa transactions (for admin/monitoring)
    """
    from .models import MpesaTransaction
    
    transactions = MpesaTransaction.objects.select_related('order').order_by('-created_at')[:50]
    
    transaction_data = []
    for transaction in transactions:
        transaction_data.append({
            'id': transaction.id,
            'phone_number': transaction.phone_number,
            'amount': str(transaction.amount),
            'status': transaction.get_status_display(),
            'checkout_request_id': transaction.checkout_request_id,
            'mpesa_receipt_number': transaction.mpesa_receipt_number or 'N/A',
            'order_reference': transaction.order.reference if transaction.order else 'N/A',
            'created_at': transaction.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'transaction_date': transaction.transaction_date.strftime('%Y-%m-%d %H:%M:%S') if transaction.transaction_date else 'N/A'
        })
    
    return render(request, 'sales/mpesa_transactions.html', {
        'transactions': transaction_data
    })

@require_http_methods(["GET"])
@login_required
def order_status(request, order_id: int):
    try:
        order = Order.objects.get(id=order_id)
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'status': order.payment_status,
            'paid_amount': str(order.paid_amount),
            'due_amount': str(order.due_amount),
            'reference': order.reference,
        })
    except Order.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Order not found'}, status=404)