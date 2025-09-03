from django import forms
from django.forms.models import inlineformset_factory
from .models import Purchase, PurchaseItem
from people.models import Supplier

class PurchaseForm(forms.ModelForm):
    supplier = forms.ModelChoiceField(
        queryset=Supplier.objects.all(),
        widget=forms.Select(attrs={'class': 'select'})
    )
    status = forms.ChoiceField(
        choices=Purchase.Status.choices,
        widget=forms.Select(attrs={'class': 'select'})
    )
    payment_status = forms.ChoiceField(
        choices=Purchase.PaymentStatus.choices,
        widget=forms.Select(attrs={'class': 'select'}),
        required=True
    )
    
    # Additional fields for UI that don't map to model
    order_tax = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        required=False,
        initial=0
    )
    discount = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        required=False,
        initial=0
    )
    shipping = forms.DecimalField(
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        required=False,
        initial=0
    )
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'id': 'summernote',
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Description (max 60 words)'
        })
    )

    class Meta:
        model = Purchase
        fields = [
            'supplier', 'status', 'payment_status'
        ]

# Custom form for PurchaseItem to ensure proper product queryset
class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseItem
        fields = ['product', 'quantity', 'unit_cost', 'discount', 'tax_amount']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'tax_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from inventory.models import Product
        self.fields['product'].queryset = Product.objects.all()
        self.fields['product'].empty_label = "Select a product"

# Inline formset for PurchaseItem
PurchaseItemFormSet = inlineformset_factory(
    Purchase,
    PurchaseItem,
    form=PurchaseItemForm,
    fields=['product', 'quantity', 'unit_cost', 'discount', 'tax_amount'],
    extra=0,  # Start with 0 extra forms since we'll add them via JS
    can_delete=True
)
