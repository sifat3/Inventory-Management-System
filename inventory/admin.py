from django.contrib import admin
from .models import Product, Inventory, Expense, PurchaseInvoice, PurchaseItem, SalesInvoice, SalesItem

admin.site.register(Product)
admin.site.register(Inventory)
admin.site.register(Expense)
admin.site.register(PurchaseInvoice)
admin.site.register(PurchaseItem)
admin.site.register(SalesInvoice)
admin.site.register(SalesItem)
