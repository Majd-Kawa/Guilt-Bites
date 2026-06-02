from django.shortcuts import render , redirect
from .models import *
from django.contrib import messages
from .utils.email_utils import send_order_confirmation, send_welcome_email
from django.http import JsonResponse
from django.core.mail import send_mail
from django.conf import settings

# Create your views here.
def is_admin(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return False
    user = User.objects.filter(id=user_id).first()
    if user and user.is_admin:
        return True
    return False

def home(request):
    categories = Category.objects.all()
    context={
        'categories' : categories
    }
    return render(request , 'home.html' , context=context)

def about_us(request):
    return render (request , 'about_us.html')

def contact_us(request):
        if request.method == 'POST':
            data = {
                'name': request.POST.get('name', ''),
                'email': request.POST.get('email', ''),
                'message': request.POST.get('message', ''),
            }
            
            errors = ContactMessage.objects.validate_message(data)
            
            if errors:
                context = {
                    'errors': errors,
                    'name': data['name'],
                    'email': data['email'],
                    'message': data['message'],
                }
                return render(request, 'contact_us.html', context)
            
            ContactMessage.objects.create_message(data)
            
            send_mail(
                subject=f"New Contact Message from {data['name']}",
                message=f"""You received a new message from your Guilt Bites contact form:

    Name: {data['name']}
    Email: {data['email']}

    Message:
    {data['message']}
    """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=True,  
            )
            
            messages.success(request, "Thank you! Your message has been saved.")
            return redirect('contact_us')

        return render (request , 'contact_us.html')

def shop_categories(request):
    categories = Category.objects.all()
    context={
        'categories' : categories
    }
    return render(request , 'categories.html' , context=context)

def shop_products(request, category_id):
    category = Category.objects.get(id=category_id)

    if category.name == "Customized Occasion Box":
        products = Product.objects.exclude(category=category)
        custom_box_product, created = Product.objects.get_or_create(
            name="Custom Occasion Box",
            defaults={
                'description': 'Create your own custom box',
                'price': 0,  
                'category': category
            }
        )
    else:
        products = Product.objects.filter(category=category)
        custom_box_product = None

    context = {
        'category': category,
        'products': products,
        'custom_box_product': custom_box_product
    }
    return render(request, 'products.html', context)

def product_details(request , product_id):
    product = Product.objects.filter(id=product_id).first()
    selectable_products = None
    if product and product.category.name == 'Customized Occasion Box':
        selectable_products = Product.objects.exclude(category__name="Customized Occasion Box")
    context = {
        'product' : product ,
        'selectable_products': selectable_products,
    }
    return render(request , 'product_details.html' , context=context)

def register(request):
    if request.method == 'POST':
        errors = User.objects.validate_data(request.POST)
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value)
            return render(request , 'register.html')
        user = User.objects.create_user(request.POST)
        request.session['user_id'] = user.id
        request.session['first_name'] = user.first_name
        request.session['last_name'] = user.last_name
        return redirect('/')
    return render(request , 'register.html')

def log_in(request):
    if request.method == 'POST':
        errors = User.objects.validate_login(request.POST)
        if len(errors) > 0:
            for key, value in errors.items():
                messages.error(request, value)
            return render(request , 'log_in.html')

        user = User.objects.get_user(request.POST)
        request.session['user_id'] = user.id
        request.session['first_name'] = user.first_name
        request.session['last_name'] = user.last_name
        request.session['is_admin'] = user.is_admin
        return redirect('/')
    return render(request , 'log_in.html')

def log_out(request):
    messages.get_messages(request)
    request.session.clear()
    return redirect('/')

def cart(request):
    cart = request.session.get('cart', {})

    items = []
    total = 0

    for key, value in cart.items():
        product_id = str(key)
        
        if isinstance(value, dict) and 'selected_products' in value:
            custom_box_product = Product.objects.filter(id=product_id).first()
            
            if not custom_box_product:
                continue
            
            subtotal = 0
            selected_items = []
            
            for item in value.get('selected_products', []):
                if isinstance(item, dict):
                    sp_id = item.get('id')
                    qty = item.get('quantity', 1)
                else:
                    sp_id = item
                    qty = 1
                
                if sp_id:
                    sp = Product.objects.filter(id=sp_id).first()
                    if sp:
                        item_subtotal = sp.price * qty
                        subtotal += item_subtotal
                        selected_items.append({
                            'product': sp,
                            'quantity': qty,
                            'subtotal': item_subtotal,
                            'name': sp.name,  
                            'id': sp.id 
                        })
            
            total += subtotal
            
            items.append({
                'product': custom_box_product,
                'quantity': 1,
                'subtotal': subtotal,
                'details': {
                    'is_custom_box': True,
                    'custom_name': value.get('custom_name', ''),
                    'event_date': value.get('event_date', ''),
                    'design_details': value.get('design_details', ''),
                    'notes': value.get('notes', ''),
                    'selected_items': selected_items
                }
            })
            
        elif isinstance(value, dict):
            product = Product.objects.filter(id=product_id).first()
            if product:
                quantity = value.get('quantity', 1)
                subtotal = product.price * quantity
                total += subtotal
                
                items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal,
                    'details': value
                })
        else:
            product = Product.objects.filter(id=product_id).first()
            if product:
                quantity = int(value)
                subtotal = product.price * quantity
                total += subtotal
                
                items.append({
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal,
                    'details': None
                })

    context = {
        'items': items,
        'total': total
    }
    return render(request, 'cart.html', context)

def add_to_cart(request, product_id):
    cart = request.session.get('cart', {})

    product = Product.objects.get(id=product_id)
    product_id = str(product_id)

    quantity = int(request.POST.get('quantity', 1))

    if product.category.name != "Customized Occasion Box":
        if product_id in cart:
            cart[product_id] += quantity
        else:
            cart[product_id] = quantity

    request.session['cart'] = cart
    return redirect('/cart')

def edit_quantity(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity'))

        cart = request.session.get('cart', {})

        if quantity > 0:
            cart[product_id] = quantity
        else:
            cart.pop(product_id, None)

        request.session['cart'] = cart
    return redirect('/cart')

def remove_from_cart(request, product_id):
    cart = request.session.get('cart', {})
    product_id = str(product_id)
    cart.pop(product_id, None)
    request.session['cart'] = cart
    return redirect('/cart')

def checkout(request):
    if 'user_id' not in request.session:
        messages.error(request, "You must log in first.")
        return redirect('/log_in')

    cart = request.session.get('cart', {})
    if not cart:
        messages.error(request, "Your cart is empty.")
        return redirect('/cart')

    user = User.objects.get(id=request.session['user_id'])
    total_price = 0

    order = Order.objects.create(user=user, total_price=0)

    for product_id_str, value in cart.items():
        product_id = int(product_id_str)

        if isinstance(value, dict) and 'selected_products' in value:
            selected_products = value.get('selected_products', [])
            
            custom_box_product = Product.objects.get(id=product_id)
            
            total_qty = sum(item["quantity"] for item in selected_products)
            
            subtotal = 0
            total_qty = 0
            selected_items_details = []
            for item in selected_products:
                sp = Product.objects.get(id=item["id"])
                qty = item["quantity"]
                item_total = sp.price * qty
                subtotal += item_total
                total_qty += qty
                selected_items_details.append({
                    'name': sp.name,
                    'quantity': qty,
                    'price': str(sp.price),
                    'total': str(item_total)
                })

            unit_price = subtotal / total_qty if total_qty > 0 else 0

            OrderItem.objects.create(
                order=order,
                product=custom_box_product,
                quantity=total_qty,
                price=unit_price,  # Store 50, not 550
                details={
                    'is_custom_box': True,
                    'custom_name': value.get('custom_name', ''),
                    'event_date': value.get('event_date', ''),
                    'design_details': value.get('design_details', ''),
                    'notes': value.get('notes', ''),
                    'selected_items': selected_items_details
                }
            )

            total_price += subtotal

        else:
            product = Product.objects.get(id=product_id)
            quantity = int(value)

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=product.price,
                details=None
            )

            total_price += product.price * quantity

    order.total_price = total_price
    order.save()

    try:
        send_order_confirmation(order)
        messages.success(request, "Order placed! Check your email for confirmation.")
    except Exception as e:
        print(f"Email sending failed: {str(e)}")
        messages.success(request, "Order placed! (Email confirmation failed)")
        

    request.session['cart'] = {}
    request.session.modified = True

    messages.success(request, "Order placed successfully!")
    return redirect('/orders')

def user_orders(request):
    if 'user_id' not in request.session:
        return redirect('/log_in')
    
    user_id=request.session['user_id']
    orders = Order.objects.filter(user_id=user_id)
    context={
        'orders' : orders,
    }
    return render(request, 'user_orders.html', context=context)

def add_category(request):
    if not is_admin(request):
        return redirect('/')

    if request.method == 'POST':
        errors = Category.objects.validate_category(request.POST, request.FILES)

        if errors:
            for key, value in errors.items():
                messages.error(request, value)
        else:
            Category.objects.category_addition(request.POST, request.FILES)
            messages.success(request, "Category added successfully!")

    return redirect('/shop/categories')

def edit_category(request, category_id):
    if not is_admin(request):
        return redirect('/')

    if request.method == 'POST':
        Category.objects.update_category(category_id, request.POST, request.FILES)

    return redirect('/shop/categories')

def delete_category(request, category_id):
    if not is_admin(request):
        return redirect('/')

    Category.objects.category_deletion(category_id)
    return redirect('/shop/categories')

def add_product(request):
    if not is_admin(request):
        return redirect('/')

    if request.method == 'POST':
        errors = Product.objects.validate_product(request.POST, request.FILES)

        if errors:
            for key, value in errors.items():
                messages.error(request, value)
        else:
            Product.objects.product_addition(request.POST, request.FILES)
            messages.success(request, "Product added successfully!")

        category_id = request.POST.get('category_id')
        return redirect(f'/shop/products/{category_id}')

    return redirect('/shop/categories')

def edit_product(request, product_id):
    if not is_admin(request):
        return redirect('/')

    if request.method == 'POST':
        Product.objects.update_product(product_id, request.POST, request.FILES)

        category_id = request.POST.get('category_id')
        return redirect(f'/shop/products/{category_id}')

    return redirect('/shop/categories')

def delete_product(request, product_id):
    if not is_admin(request):
        return redirect('/')

    category_id = request.POST.get('category_id')
    Product.objects.product_deletion(product_id)
    return redirect(f'/shop/products/{category_id}')

def manage_orders(request):
    if not is_admin(request):
        return redirect('/')

    orders = Order.objects.all()
    context={
        'orders' : orders,
    }
    return render(request, 'admin_orders.html', context=context)

def update_status(request):
    if not is_admin(request):
        return redirect('/')

    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        status = request.POST.get('status')

        Order.objects.update_order_status(order_id, status)

    return redirect('/dashboard/orders')

def delete_order(request):
    if request.method == "POST":
        order_id = request.POST.get('order_id')
        order = Order.objects.filter(id=order_id).first()
        if not order:
            messages.error(request, "Order not found.")
            return redirect('/dashboard/orders')
        
        if order.status in ["Delivered", "Cancelled"]:
            order.delete()
            messages.success(request, f"Order #{order_id} has been deleted.")
        else:
            messages.error(request, "Only Delivered or Cancelled orders can be deleted.")

    return redirect('/dashboard/orders') 

def custom_view(request):
    custom_box_category = Category.objects.get(name="Customized Occasion Box")
    return redirect(f'/shop/products/{custom_box_category.id}')

def add_custom_box_to_cart(request):
    if request.method != "POST":
        return redirect('/shop/categories')

    cart = request.session.get('cart', {})

    custom_box_product_id = request.POST.get('custom_box_product_id')

    if not custom_box_product_id:
        messages.error(request, "Custom box product ID is missing.")
        return redirect('/shop/categories')

    custom_name = request.POST.get('custom_name', '').strip()
    event_date = request.POST.get('event_date', '').strip()
    design_details = request.POST.get('design_details', '').strip()
    notes = request.POST.get('notes', '').strip()

    selected_products = []

    for product in Product.objects.all():
        qty = int(request.POST.get(f'product_{product.id}', 0))
        if qty > 0:
            selected_products.append({
                "id": product.id,
                "quantity": qty
            })

    cart[str(custom_box_product_id)] = {
        "quantity": 1,
        "selected_products": selected_products,
        "custom_name": custom_name,
        "event_date": event_date,
        "design_details": design_details,
        "notes": notes
    }

    request.session['cart'] = cart
    request.session.modified = True

    messages.success(request, "Custom box added to cart!")
    return redirect('/cart')

def order_detail(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return render(request, '404.html', {'message': 'Order not found'})
    
    return render(request, 'orders/order_detail.html', {'order': order})

def search_products(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(name__icontains=query)
    
    product_list = []
    for product in products:
        product_list.append({
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'price': str(product.price),
            'image_url': product.image.url if product.image else '',
        })

    return JsonResponse({'products': product_list})

def add_to_cart_ajax(request, product_id):
    if request.method == "POST":
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)

        if product_id_str in cart:
            if isinstance(cart[product_id_str], int):
                cart[product_id_str] += 1
        else:
            cart[product_id_str] = 1

        request.session['cart'] = cart
        total_items = sum(cart.values())
        return JsonResponse({'success': True, 'total_items': total_items})

    return JsonResponse({'error': 'Invalid request'}, status=400)