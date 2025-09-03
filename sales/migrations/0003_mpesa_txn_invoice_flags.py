from django.db import migrations, models
from decimal import Decimal

class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0002_order_mpesa_phone_number_order_mpesa_receipt_number_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mpesatransaction',
            name='applied_to_invoice',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='mpesatransaction',
            name='applied_amount',
            field=models.DecimalField(default=Decimal('0.00'), max_digits=12, decimal_places=2),
        ),
    ]