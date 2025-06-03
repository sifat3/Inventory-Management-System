from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Product, Expense, PurchaseInvoice, PurchaseItem, Inventory,SalesInvoice, SalesItem
from django.contrib import messages
from django.db import models, transaction
from django.db.models import Q
from django.db.models import Sum
from datetime import datetime



def login_view(request):
    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            error = "Invalid credentials"
    return render(request, 'inventory/login.html', {'error': error})

@login_required(login_url="/")
def dashboard_view(request):
    # Get the search query from the GET request
    query = request.GET.get('q', '')
    # Filter inventory based on the search query and quantity > 0
    if query:
        # Use Q object to search multiple fields (name, part_number, vehicle, po_number, etc.)
        inventories = Inventory.objects.filter(
            Q(product__name__icontains=query) |  # Search in product name
            Q(product__part_number__icontains=query) |  # Search in product part number
            Q(product__vehicle__icontains=query) |  # Search in product vehicle field
            Q(location__icontains=query),  # Search in product PO number field
            quantity__gt=0  # Only include products with quantity > 0
        )
    else:
        # If no search query, show products with quantity > 0
        inventories = Inventory.objects.filter(quantity__gt=0)


    if request.method == 'POST' and 'update_location' in request.POST:
        inventory_id = request.POST.get('inventory_id')
        new_location = request.POST.get('location')

        # Update the location of the inventory item
        inventory = Inventory.objects.get(id=inventory_id)
        inventory.location = new_location
        inventory.save()

        messages.success(request, f"Location updated successfully for {inventory.product.name}.")
        return redirect('dashboard')
    

    total_stock_value = sum([inventory.stock_value for inventory in Inventory.objects.all()])

    total_profit = 0
    for sale in SalesInvoice.objects.all():
        # Calculate cost of goods sold for this invoice
        cogs = sum(
            (item.product.inventory.rate + item.product.inventory.cost) * item.quantity
            for item in sale.salesitem_set.all()
        )
        profit = sale.final_amount - cogs
        total_profit += profit

    total_expenses = Expense.objects.aggregate(total=models.Sum('amount'))['total'] or 0

    # Render the dashboard template with the filtered inventories
    return render(request, 'inventory/dashboard.html', {
        'inventories': inventories,
        'total_stock_value': total_stock_value,
        'total_profit': total_profit,
        'total_expenses': total_expenses
    })



@login_required(login_url="/")
def product_list_view(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |  # Search in product name
            Q(part_number__icontains=query)  # Search in part number
        )
    else:
        products = Product.objects.all()

    return render(request, 'inventory/product_list.html', {'products': products})



# Add Product
from django.db import IntegrityError

@login_required(login_url="/")
def product_add_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        part_number = request.POST['part_number']
        au = 'au' in request.POST  # Check if 'au' checkbox is checked (Boolean Yes/No)
        vehicle = request.POST.get('vehicle', '')  # Get vehicle info (can be empty)

        try:
            Product.objects.create(name=name, part_number=part_number, au=au, vehicle=vehicle)
            messages.success(request, 'Product added successfully.')
            return redirect('product_list')
        except IntegrityError:
            messages.error(request, 'Part number must be unique. This one already exists.')
    
    return render(request, 'inventory/product_add.html')

# Edit Product
@login_required(login_url="/")
def product_edit_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.name = request.POST['name']
        product.part_number = request.POST['part_number']
        product.au = 'au' in request.POST  # Checkbox for A/U (Yes/No)
        product.vehicle = request.POST.get('vehicle', '')  # Get vehicle info (can be empty)

        try:
            product.save()
            messages.success(request, 'Product updated successfully.')
            return redirect('product_list')
        except IntegrityError:
            messages.error(request, 'Part number must be unique.')
    
    return render(request, 'inventory/product_edit.html', {'product': product})


# Delete Product
@login_required(login_url="/")
def product_delete_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, 'Product deleted.')
    return redirect('product_list')



# List all expenses
@login_required(login_url="/")
def expense_list_view(request):
    query = request.GET.get('q', '')
    if query:
        expenses = Expense.objects.filter(
            Q(reason__icontains=query) # Search in expense reason
        ).order_by('-date') 
    else:
        expenses = Expense.objects.all().order_by('-date')
    total_expense = sum(exp.amount for exp in expenses)
    return render(request, 'inventory/expense_list.html', {
        'expenses': expenses,
        'total_expense': total_expense
    })



# Add expense
@login_required(login_url="/")
def expense_add_view(request):
    if request.method == 'POST':
        date = request.POST['date']
        reason = request.POST['reason']
        amount = request.POST['amount']
        Expense.objects.create(date=date, reason=reason, amount=amount)
        messages.success(request, "Expense added successfully.")
        return redirect('expense_list')
    return render(request, 'inventory/expense_add.html')

# Edit expense
@login_required(login_url="/")
def expense_edit_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if request.method == 'POST':
        expense.date = request.POST['date']
        expense.reason = request.POST['reason']
        expense.amount = request.POST['amount']
        expense.save()
        messages.success(request, "Expense updated.")
        return redirect('expense_list')
    return render(request, 'inventory/expense_edit.html', {'expense': expense})

# Delete expense
@login_required(login_url="/")
def expense_delete_view(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    expense.delete()
    messages.success(request, "Expense deleted.")
    return redirect('expense_list')



from django.utils import timezone

# View all purchases
@login_required(login_url="/")
def purchase_list_view(request):
    query = request.GET.get('q', '')
    if query:
        purchases = PurchaseInvoice.objects.filter(
            Q(invoice_number__icontains=query)  # Search in invoice number
        ).order_by('-date')
    else:
        purchases = PurchaseInvoice.objects.all().order_by('-date')
    now = timezone.now()
    first_day_of_current_month = now.replace(day=1)
    current_month_invoices = PurchaseInvoice.objects.filter(date__gte=first_day_of_current_month)
    total_purchase_current_month = sum(
        item.total for invoice in current_month_invoices for item in PurchaseItem.objects.filter(invoice=invoice)
    )
    return render(request, 'inventory/purchase_list.html', {'purchases': purchases, 'total_purchase_current_month': total_purchase_current_month})



# Add new purchase
@login_required(login_url="/")
@transaction.atomic
def purchase_add_view(request):
    if request.method == 'POST':
        product_ids = request.POST.getlist('product')
        rates = request.POST.getlist('rate')
        costs = request.POST.getlist('cost')
        quantities = request.POST.getlist('quantity')
        remarks = request.POST.getlist('remark')
        date = request.POST.get('date')

        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        source_of_purchase = request.POST.get('source_of_purchase')
        voucher_no = request.POST.get('voucher_no')

        invoice = PurchaseInvoice.objects.create(
            name=name,
            address=address,
            phone=phone,
            source_of_purchase=source_of_purchase,
            voucher_no=voucher_no, date=date
        )

        for idx, pid in enumerate(product_ids):
            product = Product.objects.get(id=pid)
            rate = float(rates[idx])
            cost = float(costs[idx])
            qty = int(quantities[idx])
            remark = remarks[idx]

            # Save item
            PurchaseItem.objects.create(
                invoice=invoice, product=product,
                rate=rate, cost=cost, quantity=qty, remark=remark 
            )

            # Update or create inventory
            inv, created = Inventory.objects.get_or_create(product=product, defaults={
                'rate': rate,
                'cost': cost,
                'quantity': 0,
                'remark': remark
            })
            if not created:
                inv.quantity += 0
                inv.rate = rate
                inv.cost = cost
                inv.remark = remark
                inv.save()

        messages.success(request, f"Purchase Invoice #{invoice.invoice_number} created.")
        return redirect('purchase_list')

    products = Product.objects.all()
    return render(request, 'inventory/purchase_add.html', {'products': products})

# Return purchase (adjust inventory)
@login_required(login_url="/")
def purchase_return_view(request, invoice_id):
    invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)
    if request.method == 'POST':
        for item in invoice.purchaseitem_set.all():
            try:
                inv = Inventory.objects.get(product=item.product)
                inv.quantity -= item.quantity
                if inv.quantity < 0:
                    inv.quantity = 0
                inv.save()
            except Inventory.DoesNotExist:
                continue  # Should never happen
        invoice.delete()
        messages.success(request, "Purchase returned and inventory adjusted.")
        return redirect('purchase_list')

    return render(request, 'inventory/purchase_return_confirm.html', {'invoice': invoice})


# View sales invoices
@login_required(login_url="/")
def sales_list_view(request):
    query = request.GET.get('q', '')
    if query:
        sales = SalesInvoice.objects.filter(
            Q(invoice_number__icontains=query)).order_by('-date')
    else:
        sales = SalesInvoice.objects.all().order_by('-date')
    now = timezone.now()
    first_day_of_current_month = now.replace(day=1)
    current_month_invoices = SalesInvoice.objects.filter(date__gte=first_day_of_current_month)
    total_sales_current_month = sum(
        item.total for invoice in current_month_invoices for item in SalesItem.objects.filter(invoice=invoice)
    )
    return render(request, 'inventory/sales_list.html', {'sales': sales, 'total_sales_current_month': total_sales_current_month})

@login_required(login_url="/")
@transaction.atomic
def sales_add_view(request):
    if request.method == 'POST':
        product_ids = request.POST.getlist('product')
        quantities = request.POST.getlist('quantity')
        prices = request.POST.getlist('price')
        remarks = request.POST.getlist('remark')
        it_numbers = request.POST.getlist('it_no')
        
        # Get initial amount paid, default 0 if not provided
        amount_paid = float(request.POST.get('amount_paid', 0))

        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        date = request.POST.get('date')

        from decimal import Decimal, InvalidOperation

        discount_str = request.POST.get('discount', '0').strip()
        amount_paid_str = request.POST.get('amount_paid', '0').strip()

        try:
            discount = Decimal(discount_str) if discount_str else Decimal('0.00')
        except InvalidOperation:
            discount = Decimal('0.00')

        try:
            amount_paid = Decimal(amount_paid_str) if amount_paid_str else Decimal('0.00')
        except InvalidOperation:
            amount_paid = Decimal('0.00')



        # Create SalesInvoice with amount_paid initialized
        invoice = SalesInvoice.objects.create(
            name=name,
            address=address,
            phone=phone,
            amount_paid=amount_paid,
            discount=discount, date=date
        )

        for idx, pid in enumerate(product_ids):
            product = Product.objects.get(id=pid)
            quantity = int(quantities[idx])
            price = float(prices[idx])
            remark = remarks[idx]
            it_no = it_numbers[idx]

            # Create sale item
            SalesItem.objects.create(
                invoice=invoice,
                product=product,
                quantity=quantity,
                selling_price=price,
                remark=remark,
                it_no=it_no
            )

            # Update inventory
            try:
                inventory = Inventory.objects.get(product=product)
                inventory.quantity -= quantity
                if inventory.quantity < 0:
                    inventory.quantity = 0
                inventory.save()
            except Inventory.DoesNotExist:
                continue

        # Save invoice to update total_amount and due_amount
        invoice.save()

        messages.success(request, f"Sales Invoice #{invoice.invoice_number} created with due ৳{invoice.due_amount}.")
        return redirect('sales_list')

    products = Inventory.objects.filter(quantity__gt=0).select_related('product')
    return render(request, 'inventory/sales_add.html', {'products': products})

@login_required(login_url="/")
def sales_due_received_view(request, invoice_id):
    invoice = get_object_or_404(SalesInvoice, id=invoice_id)
    if invoice.due_amount <= 0:
        messages.info(request, "No due payment pending for this invoice.")
        return redirect('sales_list')

    if request.method == 'POST':
        invoice.amount_paid += invoice.due_amount
        invoice.due_amount = 0.00
        invoice.save()
        messages.success(request, f"Due payment for Invoice #{invoice.invoice_number} received successfully.")
        return redirect('sales_list')

    return render(request, 'inventory/sales_due_received_confirm.html', {'invoice': invoice})

# Return a sale (restock inventory)
@login_required(login_url="/")
def sales_return_view(request, invoice_id):
    invoice = get_object_or_404(SalesInvoice, id=invoice_id)
    if request.method == 'POST':
        for item in invoice.salesitem_set.all():
            inv, created = Inventory.objects.get_or_create(product=item.product)
            inv.quantity += item.quantity
            inv.save()
        invoice.delete()
        messages.success(request, "Sale returned and inventory restored.")
        return redirect('sales_list')
    return render(request, 'inventory/sales_return_confirm.html', {'invoice': invoice})

@login_required(login_url="/")
def sales_invoice_view(request, invoice_id):
    # Get the invoice and its associated items
    invoice = get_object_or_404(SalesInvoice, id=invoice_id)
    items = invoice.salesitem_set.all()

    # Calculate the total
    total = sum(item.total for item in items)

    # Ensure you're passing all necessary data to the template
    return render(request, 'inventory/sales_invoice.html', {
        'invoice': invoice,
        'items': items,
        'total': total
    })


@login_required(login_url="/")
def purchase_invoice_view(request, invoice_id):
    invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)
    items = invoice.purchaseitem_set.all()
    total = sum(item.total for item in items)
    return render(request, 'inventory/purchase_invoice.html', {
        'invoice': invoice,
        'items': items,
        'total': total,
    })


def sales_invoice_print_view(request, invoice_id):
    invoice = get_object_or_404(SalesInvoice, id=invoice_id)
    items = invoice.salesitem_set.all()
    total = sum(item.total for item in items)

    return render(request, 'inventory/sales_invoice_print.html', {
        'invoice': invoice,
        'items': items,
        'total': total
    })


def purchase_invoice_print_view(request, invoice_id):
    invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)
    items = invoice.purchaseitem_set.all()
    total = sum(item.total for item in items)

    return render(request, 'inventory/purchase_invoice_print.html', {
        'invoice': invoice,
        'items': items,
        'total': total
    })



def purchase_invoice_received_view(request, invoice_id):
    # Get the purchase invoice and related items
    invoice = get_object_or_404(PurchaseInvoice, id=invoice_id)
    items = invoice.purchaseitem_set.all()

    # Iterate over each item to mark it as received and update the inventory
    for item in items:
        if not item.received:  # Only process if the item is not yet received
            item.received = True  # Mark the item as received
            item.save()

            # Update the inventory quantity
            inventory, created = Inventory.objects.get_or_create(product=item.product)
            inventory.quantity += item.quantity  # Increase inventory quantity
            inventory.save()
    invoice.received = True
    invoice.save()

    # Success message and redirect
    messages.success(request, f"Products for Purchase Invoice #{invoice.invoice_number} have been marked as received.")
    return redirect("purchase_list") 




from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.shortcuts import render
from .models import SalesInvoice

@login_required(login_url="/")
def sales_report_view(request):
    sales = SalesInvoice.objects.none()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            sales = SalesInvoice.objects.filter(date__date__gte=start, date__date__lte=end).order_by('date')
        except Exception:
            sales = SalesInvoice.objects.none()

    context = {
        'sales': sales,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'inventory/sales_report.html', context)


from django.db.models import Sum, F

@login_required(login_url="/")
def purchase_report_view(request):
    purchases = PurchaseInvoice.objects.none()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            purchases = PurchaseInvoice.objects.filter(
                date__date__gte=start,
                date__date__lte=end
            ).annotate(
                total_amount=Sum(F('purchaseitem__quantity') * F('purchaseitem__rate'))
            )
        except ValueError:
            purchases = PurchaseInvoice.objects.none()

    context = {
        'purchases': purchases,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'inventory/purchase_report.html', context)



from django.db.models import Sum

@login_required(login_url="/")
def expense_report_view(request):
    expenses = Expense.objects.none()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    total_amount = 0

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            expenses = Expense.objects.filter(date__gte=start, date__lte=end).order_by('date')

            total_amount = expenses.aggregate(total=Sum('amount'))['total'] or 0
        except ValueError:
            expenses = Expense.objects.none()
            total_amount = 0

    context = {
        'expenses': expenses,
        'total_amount': total_amount,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'inventory/expense_report.html', context)


from django.db.models import F, ExpressionWrapper, DecimalField, Sum
from datetime import datetime

@login_required(login_url="/")
def inventory_report_view(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    purchases = PurchaseInvoice.objects.none()
    sales = SalesInvoice.objects.none()
    expenses = Expense.objects.none()

    total_buy = total_sell = total_expenses = total_profit = 0

    if start_date and end_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')

            # Filter the invoices by date range for display
            purchases = PurchaseInvoice.objects.filter(date__gte=start, date__lte=end)
            sales = SalesInvoice.objects.filter(date__gte=start, date__lte=end)
            expenses = Expense.objects.filter(date__gte=start, date__lte=end)

            # Calculate total purchase amount by summing (quantity * rate) over purchase items
            total_buy = PurchaseInvoice.objects.filter(date__gte=start, date__lte=end).annotate(
                invoice_total=Sum(
                    ExpressionWrapper(
                        F('purchaseitem__quantity') * F('purchaseitem__rate'),
                        output_field=DecimalField()
                    )
                )
            ).aggregate(total=Sum('invoice_total'))['total'] or 0

            # Calculate total sales amount similarly
            total_sell = SalesInvoice.objects.filter(date__gte=start, date__lte=end).annotate(
                invoice_total=Sum(
                    ExpressionWrapper(
                        F('salesitem__quantity') * F('salesitem__selling_price'),
                        output_field=DecimalField()
                    )
                )
            ).aggregate(total=Sum('invoice_total'))['total'] or 0

            total_expenses = expenses.aggregate(total=Sum('amount'))['total'] or 0

            total_profit = total_sell - total_buy - total_expenses

        except ValueError:
            purchases = SalesInvoice.objects.none()
            sales = SalesInvoice.objects.none()
            expenses = Expense.objects.none()
            total_buy = total_sell = total_expenses = total_profit = 0

    return render(request, 'inventory/inventory_report.html', {
        'purchases': purchases,
        'sales': sales,
        'expenses': expenses,
        'total_buy': total_buy,
        'total_sell': total_sell,
        'total_expenses': total_expenses,
        'total_profit': total_profit,
        'start_date': start_date,
        'end_date': end_date,
    })


