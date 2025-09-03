from django.db import models
from people.models import Supplier
from inventory.models import Product
from decimal import Decimal
import uuid
# Create your models here.
class Purchase(models.Model):
    class Status(models.TextChoices):
        DRAFT    = 'draft',    'Draft'
        ORDERED  = 'ordered',  'Ordered'
        RECEIVED = 'received', 'Received'
        CANCELED = 'canceled', 'Canceled'

    class PaymentStatus(models.TextChoices):
        PAID = 'paid', 'Paid'
        NOT_PAID = 'not_paid', 'Not Paid'

    supplier      = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchases')
    reference     = models.CharField(max_length=64, unique=True, blank=True)
    order_date    = models.DateField(auto_now_add=True)
    receive_date  = models.DateField(null=True, blank=True)
    status        = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.NOT_PAID)
    grand_total   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    due_amount    = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ['-order_date', 'reference']

    def __str__(self):
        return f"PO {self.reference} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        if not self.reference:
            # Generate unique reference
            import datetime
            today = datetime.date.today()
            prefix = f"PO{today.strftime('%Y%m%d')}"
            
            # Find the highest number for today
            existing_refs = Purchase.objects.filter(
                reference__startswith=prefix
            ).values_list('reference', flat=True)
            
            max_num = 0
            for ref in existing_refs:
                try:
                    num = int(ref.replace(prefix, ''))
                    max_num = max(max_num, num)
                except ValueError:
                    continue
            
            self.reference = f"{prefix}{max_num + 1:03d}"
        
        super().save(*args, **kwargs)

    def update_totals(self):
        total = sum(item.total_cost for item in self.items.all())
        self.grand_total = total
        self.due_amount = max(total - self.paid_amount, Decimal('0.00'))
        if self.paid_amount >= total:
            # you might have a PaymentStatus field too…
            pass
        self.save()

class PurchaseItem(models.Model):
    purchase       = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    product        = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity       = models.PositiveIntegerField()
    unit_cost      = models.DecimalField(max_digits=10, decimal_places=2)
    discount       = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount     = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost     = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Calculate total cost: (quantity * unit_cost) - discount + tax_amount
        line_total = (self.quantity * self.unit_cost) - self.discount + self.tax_amount
        self.total_cost = max(line_total, Decimal('0.00'))  # Ensure non-negative
        
        super().save(*args, **kwargs)
        
        # Update stock and parent totals
        if hasattr(self, 'product') and self.product:
            # Get or create stock entry for this product
            from inventory.models import Stock
            stock, created = Stock.objects.get_or_create(
                product=self.product,
                defaults={'quantity': 0, 'price': self.unit_cost, 'tax': 0, 'discount': 0, 'quantity_alert': 0}
            )
            stock.quantity += self.quantity
            stock.save()
            
        if hasattr(self, 'purchase') and self.purchase:
            self.purchase.update_totals()