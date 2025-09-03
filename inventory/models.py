from django.db import models
import uuid
from django.utils.text import slugify

# Create your models here.

class Category(models.Model):
    name = models.TextField()
    slug = models.SlugField()
    status = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
    def image(self):
        
        first_product = self.products.first()
        if not first_product:
            return None

        gallery_item = first_product.images.first()
        if gallery_item and gallery_item.image:
            return gallery_item.image.url

        return None
    
class SubCategory(models.Model):
    category = models.ForeignKey(Category,related_name='sub_categories',on_delete=models.CASCADE)
    name = models.TextField()
    slug = models.SlugField()
    image = models.ImageField(upload_to='subcategory-images/')
    description = models.TextField(default='')
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Unit(models.Model):
    name = models.TextField()
    short_name = models.CharField(max_length=12)
    status = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Variant(models.Model):
    name = models.TextField()
    values = models.TextField()
    status = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name 
    
class Product(models.Model):
    class SellingType(models.TextChoices):
        ONLINE = 'online', 'Online'
        POS = 'pos', 'POS'

    name = models.TextField()
    slug = models.SlugField(unique=True)
    sku = models.TextField(unique=True,blank=True)
    selling_type = models.CharField(
        max_length=10,
        choices=SellingType.choices,
        default=SellingType.ONLINE,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='products',
        null=True
    )
    sub_category = models.ForeignKey(
        SubCategory,
        on_delete=models.SET_NULL,
        related_name='products',
        null=True
    )
    units = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        related_name='products',
        null=True
    )
    description = models.TextField(blank=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="The purchase/cost price of the product")

    def save(self, *args, **kwargs):
        # Generate slug from name if not provided
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Generate SKU if not provided
        if not self.sku:
            # Generate a short UUID-based SKU
            self.sku = str(uuid.uuid4())[:8].upper()
            # Ensure uniqueness
            while Product.objects.filter(sku=self.sku).exists():
                self.sku = str(uuid.uuid4())[:8].upper()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
    def first_image_url(self):
        """
        Return the URL (string) of the first ProductGallery image, or an empty string.
        """
        gallery_item = ProductGallery.objects.filter(product=self).first()
        if gallery_item and gallery_item.image:
            return gallery_item.image.url
        return ""

    def stock(self):
        return self.stock_entries.first()

class Stock(models.Model):
    class TaxType(models.TextChoices):
        EXCLUSIVE = 'exclusive', 'Exclusive'
        INCLUSIVE = 'inclusive', 'Inclusive'

    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Percentage'
        FIXED = 'fixed', 'Fixed'

    product = models.ForeignKey(
        Product,
        related_name='stock_entries',
        on_delete=models.CASCADE
    )
    quantity = models.IntegerField(default=0)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    tax_type = models.CharField(
        max_length=10,
        choices=TaxType.choices,
        default=TaxType.EXCLUSIVE,
    )
    tax = models.IntegerField(help_text="Tax rate as a percentage or fixed amount based on tax_type")
    discount_type = models.CharField(
        max_length=10,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE,
    )
    discount = models.IntegerField(help_text="Discount rate as a percentage or fixed amount based on discount_type")
    quantity_alert = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - Stock"

class ProductGallery(models.Model):
    product = models.ForeignKey(Product,related_name='images',on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product-images/')

    def __str__(self):
        return self.product.name