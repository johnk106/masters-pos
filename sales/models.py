from django.db import models
from django.conf import settings
from decimal import Decimal
from people.models import *
from django.utils import timezone

from inventory.models import Product    # assuming Product lives in inventory app


class Order(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        COMPLETED = 'completed', 'Completed'
        CANCELED  = 'canceled',  'Canceled'
        FAILED    = 'failed',    'Failed'

    class PaymentStatus(models.TextChoices):
        UNPAID     = 'unpaid',     'Unpaid'
        PARTIAL    = 'partial',    'Partial'
        PAID       = 'paid',       'Paid'
        OVERPAID   = 'overpaid',   'Overpaid'

    class PaymentMethod(models.TextChoices):
        CASH      = 'cash',      'Cash'
        MPESA     = 'mpesa',     'M-Pesa'

    customer       = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        related_name='orders'
    )
    reference      = models.CharField(max_length=64, unique=True)
    date           = models.DateField(auto_now_add=True)
    status         = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT
    )
    grand_total    = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    paid_amount    = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    due_amount     = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    mpesa_phone_number = models.CharField(max_length=15, blank=True, null=True, help_text="M-Pesa phone number used for payment")
    mpesa_receipt_number = models.CharField(max_length=20, blank=True, null=True, help_text="M-Pesa receipt number")
    biller         = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # or an Employee model if separate
        on_delete=models.SET_NULL,
        null=True,
        related_name='billed_orders'
    )
    source         = models.CharField(
        max_length=32,
        help_text="e.g. 'pos', 'online', 'phone', etc."
    )

    class Meta:
        ordering = ['-date', 'reference']

    def __str__(self):
        return f"Order {self.reference} ({self.status})"

    def update_totals(self):
        """
        Recalculate grand_total, paid_amount, due_amount, and payment_status
        based on related OrderItem lines and payments record (if any).
        """
        items = self.items.all()
        total = sum(item.total_cost for item in items)
        self.grand_total = total
        # paid_amount is presumably updated by payment logic elsewhere
        self.due_amount = max(self.grand_total - self.paid_amount, Decimal('0.00'))

        if self.paid_amount >= self.grand_total:
            self.payment_status = self.PaymentStatus.PAID
        elif 0 < self.paid_amount < self.grand_total:
            self.payment_status = self.PaymentStatus.PARTIAL
        else:
            self.payment_status = self.PaymentStatus.UNPAID

        self.save()


class OrderItem(models.Model):
    product        = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    order          = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount       = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Line‐item discount amount"
    )
    tax            = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Tax rate as a percentage (e.g. 10.00 for 10%)"
    )
    tax_amount     = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Monetary tax amount for this line"
    )
    unit_cost      = models.DecimalField(max_digits=10, decimal_places=2)
    quantity       = models.PositiveIntegerField(default=1)
    total_cost     = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="(unit_cost * quantity) - discount + tax_amount"
    )

    class Meta:
        unique_together = ('order', 'product')

    def __str__(self):
        return f"{self.product.name} x {self.quantity} (Order {self.order.reference})"

    def calculate_totals(self):
        """
        Compute tax_amount and total_cost from purchase_price, discount, tax, and quantity.
        """
        # Example: if tax is a percentage
        line_subtotal = (self.purchase_price * self.quantity) - self.discount
        computed_tax_amount = (line_subtotal * self.tax) / Decimal('100.00')
        self.tax_amount = computed_tax_amount.quantize(Decimal('0.01'))
        self.total_cost = (line_subtotal + self.tax_amount).quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        self.calculate_totals()
        super().save(*args, **kwargs)
        # After saving, update the parent Order totals
        self.order.update_totals()


class Invoice(models.Model):
    class Status(models.TextChoices):
        DRAFT     = 'draft',     'Draft'
        OPEN      = 'open',      'Open'
        PAID      = 'paid',      'Paid'
        OVERDUE   = 'overdue',   'Overdue'
        CANCELED  = 'canceled',  'Canceled'

    invoice_no    = models.CharField(max_length=64, unique=True)
    customer      = models.ForeignKey(
        Customer,
        on_delete=models.SET_NULL,
        null=True,
        related_name='invoices'
    )
    due_date      = models.DateField()
    amount        = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    amount_paid   = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    amount_due    = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    status        = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT
    )
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at', 'invoice_no']

    def __str__(self):
        return f"Invoice {self.invoice_no} ({self.status})"

    def update_amounts(self):
        """
        Recalculate amount, amount_due, and status based on related InvoiceItems and payments.
        """
        total = sum(item.total for item in self.items.all())
        self.amount      = total
        self.amount_due  = max(self.amount - self.amount_paid, Decimal('0.00'))

        today = timezone.now().date()

        if self.amount_paid >= self.amount:
            self.status = self.Status.PAID
        elif self.amount_due > Decimal('0.00') and self.due_date < today:
            self.status = self.Status.OVERDUE
        else:
            self.status = self.Status.OPEN

        # Only update the status and amounts fields for efficiency
        self.save(update_fields=['amount', 'amount_paid', 'amount_due', 'status'])


class InvoiceItem(models.Model):
    invoice   = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product   = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='invoice_items'
    )
    quantity  = models.PositiveIntegerField(default=1)
    cost      = models.DecimalField(max_digits=10, decimal_places=2)  # unit cost
    discount  = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Line‐item discount (absolute amount)"
    )
    total     = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="(cost * quantity) - discount"
    )

    class Meta:
        unique_together = ('invoice', 'product')

    def __str__(self):
        return f"{self.product.name} x {self.quantity} (Invoice {self.invoice.invoice_no})"

    def calculate_total(self):
        subtotal = (self.cost * self.quantity) - self.discount
        self.total = subtotal.quantize(Decimal('0.01'))

    def save(self, *args, **kwargs):
        self.calculate_total()
        super().save(*args, **kwargs)
        # After saving, update the parent Invoice amounts
        self.invoice.update_amounts()


class MpesaTransaction(models.Model):
    class Status(models.TextChoices):
        PENDING    = 'pending',    'Pending'
        SUCCESSFUL = 'successful', 'Successful'
        FAILED     = 'failed',     'Failed'
        CANCELLED  = 'cancelled',  'Cancelled'

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='mpesa_transactions',
        null=True,
        blank=True
    )
    phone_number = models.CharField(max_length=15, help_text="Phone number used for M-Pesa payment")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Transaction amount")
    merchant_request_id = models.CharField(max_length=50, unique=True, help_text="M-Pesa Merchant Request ID")
    checkout_request_id = models.CharField(max_length=50, unique=True, help_text="M-Pesa Checkout Request ID")
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.PENDING
    )
    mpesa_receipt_number = models.CharField(max_length=20, blank=True, null=True, help_text="M-Pesa receipt number")
    transaction_date = models.DateTimeField(blank=True, null=True, help_text="Date when M-Pesa transaction was completed")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Additional fields for debugging and tracking
    response_code = models.CharField(max_length=10, blank=True, null=True)
    response_description = models.TextField(blank=True, null=True)
    customer_message = models.TextField(blank=True, null=True)

    # Idempotency / application tracking
    applied_to_invoice = models.BooleanField(default=False)
    applied_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['merchant_request_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"M-Pesa Transaction {self.checkout_request_id} - {self.status}"
