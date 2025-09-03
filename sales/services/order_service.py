import json,random
from decimal import Decimal

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.conf import settings

from sales.models import Order, OrderItem, Invoice, InvoiceItem  
from inventory.models import Product
from people.models import Customer 
from authentication.models import  UserProfile


class InvoiceManager:
    @staticmethod
    def create_invoice(order: Order) -> Invoice:
        """
        Given a completed Order, create an associated Invoice and InvoiceItems.
        Returns the new Invoice instance.
        """
        # 1) Build a unique invoice number, e.g. "INV-<order.reference>"
        invoice_no = f"INV-{order.reference}"

        # 2) Determine amounts from the order
        total_amount = order.grand_total
        amount_paid = order.paid_amount
        amount_due = order.due_amount

        # 3) Determine status based on amount_due
        if amount_paid >= total_amount:
            status = Invoice.Status.PAID
        elif amount_due > 0 and timezone.now().date() > order.date:
            status = Invoice.Status.OVERDUE
        else:
            status = Invoice.Status.OPEN

        # 4) Create Invoice
        invoice = Invoice.objects.create(
            invoice_no=invoice_no,
            customer=order.customer,
            due_date=timezone.now().date(),  # or set a due date policy
            amount=total_amount,
            amount_paid=amount_paid,
            amount_due=amount_due,
            status=status
        )

        # 5) Create InvoiceItems by copying OrderItems
        for oi in order.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                product=oi.product,
                quantity=oi.quantity,
                cost=oi.unit_cost,
                discount=oi.discount
                # total will be computed in InvoiceItem.save()
            )

        # 6) Recompute invoice amounts & status
        invoice.update_amounts()

        return invoice


class OrderManager:
    @staticmethod
    def create_order(request):
        import traceback
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Removed debug prints - order creation working correctly
        
        try:
            # Parse JSON data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({"success": False, "error": "Invalid JSON payload."}, status=400)

            # 1) Extract top-level fields
            customer_id = data.get("customer_id")
            reference   = data.get("reference", "").strip()
            source      = data.get("source", "").strip()
            payment_method = data.get("payment_method", "cash").strip()
            items       = data.get("items", [])

            # 2) Auto-generate reference if blank
            if not reference:
                now = timezone.now()
                timestamp = now.strftime("%Y%m%d-%H%M%S")
                rand4 = random.randint(1000, 9999)
                reference = f"ORD-{timestamp}-{rand4}"

            # 3) Validate source and items
            if not source:
                return JsonResponse({"success": False, "error": "Source is required."}, status=400)
            if not isinstance(items, list) or not items:
                return JsonResponse({"success": False, "error": "Order must include at least one item."}, status=400)

            # 4) Fetch customer if provided
            customer = None
            if customer_id is not None:
                try:
                    # Accept numeric strings or ints
                    if isinstance(customer_id, str) and customer_id.strip() == '':
                        customer = None
                    elif isinstance(customer_id, str) and customer_id.isdigit():
                        customer = Customer.objects.get(id=int(customer_id))
                    elif isinstance(customer_id, int):
                        customer = Customer.objects.get(id=customer_id)
                    else:
                        # Treat any non-numeric string as a customer name fallback
                        name_value = str(customer_id).strip()
                        if name_value:
                            customer, _ = Customer.objects.get_or_create(name=name_value)
                        else:
                            customer = None
                except Customer.DoesNotExist:
                    return JsonResponse({"success": False, "error": "Customer not found."}, status=404)

            # 5) Create the Order
            order = Order.objects.create(
                customer=customer,
                reference=reference,
                date=timezone.now().date(),
                status=Order.Status.COMPLETED,
                grand_total=Decimal('0.00'),
                paid_amount=Decimal('0.00'),
                due_amount=Decimal('0.00'),
                payment_status=Order.PaymentStatus.UNPAID,
                payment_method=payment_method,
                biller=request.user if request.user.is_authenticated else None,
                source=source
            )

            # 6) Process each item
            for idx, item_data in enumerate(items):
                product_id     = item_data.get("product_id")
                purchase_price = item_data.get("purchase_price")
                discount       = item_data.get("discount", "0.00")
                tax            = item_data.get("tax", "0.00")
                quantity       = item_data.get("quantity")

                # Validate required fields
                if product_id is None or purchase_price is None or quantity is None:
                    order.delete()
                    return JsonResponse({
                        "success": False,
                        "error": f"Item #{idx+1} missing required fields."
                    }, status=400)

                # Lookup product
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    order.delete()
                    return JsonResponse({
                        "success": False,
                        "error": f"Product with ID {product_id} not found."
                    }, status=404)

                # Parse numerics
                try:
                    purchase_price = Decimal(str(purchase_price))
                    discount       = Decimal(str(discount))
                    tax            = Decimal(str(tax))
                    quantity       = int(quantity)
                except (ValueError, TypeError):
                    order.delete()
                    return JsonResponse({
                        "success": False,
                        "error": f"Invalid numeric value on item #{idx+1}."
                    }, status=400)

                # Save the item (assumes your OrderItem.save() updates order totals)
                OrderItem.objects.create(
                    product=product,
                    order=order,
                    purchase_price=purchase_price,
                    discount=discount,
                    tax=tax,
                    unit_cost=purchase_price,
                    quantity=quantity
                )
                stock_obj = product.stock()
                stock_obj.quantity -= quantity
                stock_obj.save(update_fields=['quantity'])
            

            # 7) Handle optional payment
            paid_amount = data.get("paid_amount")
            payment_details = data.get("payment_details", {})
            if paid_amount is not None:
                try:
                    paid_decimal = Decimal(str(paid_amount))
                    order.paid_amount = paid_decimal
                    order.due_amount = max(order.grand_total - paid_decimal, Decimal('0.00'))
                    if paid_decimal >= order.grand_total:
                        order.payment_status = Order.PaymentStatus.PAID
                    elif paid_decimal > Decimal('0.00'):
                        order.payment_status = Order.PaymentStatus.PARTIAL
                    else:
                        order.payment_status = Order.PaymentStatus.UNPAID
                    order.save()
                except (ValueError, TypeError):
                    pass  # ignore invalid paid_amount

            # 8) Generate invoice
            invoice = InvoiceManager.create_invoice(order)

            # 9) Return success
            return JsonResponse({
                "success": True,
                "order_id": order.id,
                "invoice_id": invoice.id,
                "invoice_no": invoice.invoice_no,
                "reference": reference
            })
            
        except Exception as e:
            # Log the error for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating order: {str(e)}", exc_info=True)
            
            # Return a 500 error with details
            return JsonResponse({
                "success": False,
                "error": "Internal server error occurred while creating order.",
                "details": str(e) if settings.DEBUG else "Contact support for assistance."
            }, status=500)
