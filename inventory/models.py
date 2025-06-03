from django.db import models
import datetime
from decimal import Decimal


class Product(models.Model):
    name = models.CharField(max_length=100)
    part_number = models.CharField(max_length=100, unique=True)
    au = models.BooleanField(default=False)  # A/U: Boolean Yes/No
    vehicle = models.CharField(max_length=100, blank=True)  # Vehicle field (optional)

    def __str__(self):
        return f"{self.name} ({self.part_number})"

class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=255, blank=True, null=True)
    remark = models.TextField(null=True, blank=True) 

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
    date = models.DateTimeField()
    name = models.CharField(max_length=100)  # Name
    address = models.TextField()  # Address
    phone = models.CharField(max_length=15)  # Phone
    source_of_purchase = models.CharField(max_length=100)  # Source of Purchase
    voucher_no = models.CharField(max_length=50)  # Voucher No.
    received = models.BooleanField(default=False)  # Track if item is received
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)

    def __str__(self):
        return f"Purchase Invoice #{self.invoice_number}"
    
    def save(self, *args, **kwargs):
        # Generate the invoice number only if it's a new instance (no invoice_number set yet)
        if not self.invoice_number:
            # Get the current year and month
            year = str(datetime.datetime.now().year)[2:]  # Last 2 digits of the year
            month = datetime.datetime.now().strftime('%m')  # 2-digit month
            prefix = 'B'  # Purchase invoice prefix

            # Get the last invoice number to generate the next serial number
            last_invoice = PurchaseInvoice.objects.filter(date__year=datetime.datetime.now().year).order_by('-id').first()

            if last_invoice:
                # Get the last serial number and increment it by 1
                serial_number = int(last_invoice.invoice_number[-2:]) + 1
            else:
                serial_number = 1  # If no invoices exist, start from 1

            # Format the invoice number (B2505X18)
            self.invoice_number = f"{prefix}{year}{month}{str(serial_number).zfill(2)}"

        super(PurchaseInvoice, self).save(*args, **kwargs)



class PurchaseItem(models.Model):
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    received = models.BooleanField(default=False)  # Track if item is received
    remark = models.TextField(null=True, blank=True) 

    @property
    def chs(self):
        return self.rate + self.cost

    @property
    def total(self):
        return self.chs * self.quantity

class SalesInvoice(models.Model):
    date = models.DateTimeField()
    name = models.CharField(max_length=100)  # Name
    address = models.TextField()  # Address
    phone = models.CharField(max_length=15)  # Phone
    invoice_number = models.CharField(max_length=20, unique=True, blank=True)

    # Added fields to track payments and due
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    due_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    @property
    
    def final_amount(self):
        # Make sure total_amount and discount are Decimal
        total = Decimal(self.total_amount)
        discount = Decimal(self.discount) if self.discount else Decimal('0.00')
        result = total - discount
        return result if result > 0 else Decimal('0.00')


    def __str__(self):
        return f"Sales Invoice #{self.invoice_number}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            year = str(datetime.datetime.now().year)[2:]  # Last 2 digits of the year
            month = datetime.datetime.now().strftime('%m') 
            prefix = 'S'  # Sales invoice prefix

            last_invoice = SalesInvoice.objects.filter(date__year=datetime.datetime.now().year).order_by('-id').first()

            if last_invoice:
                serial_number = int(last_invoice.invoice_number[-2:]) + 1
            else:
                serial_number = 1

            self.invoice_number = f"{prefix}{year}{month}{str(serial_number).zfill(2)}"

        # Update total_amount based on related SalesItems if the invoice exists
        if self.pk:
            total = sum(item.total for item in self.salesitem_set.all())
            self.total_amount = total

        # Update due amount based on total after discount
        self.due_amount = self.final_amount - self.amount_paid

        super(SalesInvoice, self).save(*args, **kwargs)


class SalesItem(models.Model):
    invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    remark = models.TextField(null=True, blank=True)  # Remark field for the Sell (Sales)
    it_no = models.CharField(max_length=100, blank=True, null=True)

    @property
    def total(self):
        return self.selling_price * self.quantity
