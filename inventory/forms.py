from django import forms
from .models import Product, Expense, Purchase, Sale

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'part_number']

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['date', 'reason', 'amount']

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['invoice_number', 'date', 'total_amount']

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ['invoice_number', 'date', 'total_amount']
