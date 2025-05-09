from django.db import models

class Product(models.Model):
    name = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100, unique=True)
    au = models.BooleanField(default=False)  # A/U: Boolean Yes/No
    vehicle = models.CharField(max_length=100, blank=True)  # Vehicle field (optional)
    po_number = models.CharField(max_length=100, blank=True)  # PO No. field (optional)

    def __str__(self):
        return f"{self.name} ({self.part_number})"

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def chs(self):
        return self.rate + self.cost

    @property
    def stock_value(self):
        return self.chs * self.quantity

class Expense(models.Model):
    date = models.DateField()
    reason = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.date} - {self.reason} - ৳{self.amount}"

class PurchaseInvoice(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    received = models.BooleanField(default=False)  # Track if item is received
    remark = models.TextField(null=True, blank=True)  # Optional field for remarks

    def __str__(self):
        return f"Invoice #{self.id} - {self.date.strftime('%Y-%m-%d')}"

class PurchaseItem(models.Model):
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    received = models.BooleanField(default=False)  # Track if item is received

    @property
    def chs(self):
        return self.rate + self.cost

    @property
    def total(self):
        return self.chs * self.quantity

class SalesInvoice(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    tt = models.TextField(null=True, blank=True)
    remark = models.TextField(null=True, blank=True)  # Optional field for remarks


    def __str__(self):
        return f"Sales Invoice #{self.id} - TT: {self.tt}"

class SalesItem(models.Model):
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def total(self):
        return self.selling_price * self.quantity
