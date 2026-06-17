from django.db import models
import re
import datetime
import bcrypt
from decimal import Decimal


EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
PHONE_REGEX = re.compile(r'^\+?[\d\s-]{9,20}$')

class UserValidator(models.Manager):
    def validate_data(self, data):
        errors={}
        first_name = data.get('first_name' , '').strip()
        if not first_name:
            errors['first_name'] = 'First name is required.'
        elif len(first_name) <= 2:
            errors['first_name'] = 'First name must be at least 2 characters long.'
        last_name = data.get('last_name' , '').strip()
        if not last_name:
            errors['last_name'] = 'Last name is required.'
        elif len(last_name) <= 2:
            errors['last_name'] = 'Last name must be at least 2 characters long.'
        email = data.get('email' , '').strip()
        if not email:
            errors['email'] = 'Email address is required.'
        elif not EMAIL_REGEX.match(email):
            errors['email'] = 'Invalid email'
        elif User.objects.filter(email=email).first():
            errors['email'] = 'This email address already exists. Please revise and try again.'
        password = data.get('password', '').strip()
        confirm_password=data.get('confirm_password', '').strip()
        if not password:
            errors['password'] = 'Password is required.'
        elif len(password) < 7 :
            errors['password'] = 'Password must be at least 7 characters.'
        if password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'
        date_of_birth = data.get('date_of_birth' , '')
        if not date_of_birth:
            errors['date_of_birth'] = 'Date of Birth is required.'
        elif date_of_birth:
            date_of_birth= datetime.datetime.strptime(date_of_birth,'%Y-%m-%d').date()
            today=datetime.date.today()
            age = (today - date_of_birth).days // 365
            if date_of_birth > today:
                errors['date_of_birth'] = 'Date of Birth cannot be in the future. Please enter a valid Date of Birth.'
            elif age < 13: 
                errors['date_of_birth'] = 'Sorry, you don’t meet the minimum age requirement to continue. This website is only available to users aged 13 and above'
        location = data.get('location' , '').strip()
        if not location:
            errors['location'] = 'Location is required.'
        elif len(location) < 10:
            errors['location'] = 'Location is too short. Please be more specific.'
        phone_number = data.get('phone_number' , '').strip()
        if not phone_number:
            errors['phone_number'] = 'Phone number is required.'
        elif not PHONE_REGEX.match(phone_number):
            errors['phone_number'] = 'Invalid phone number. Use format like +970 599-123-456.'
        if 'is_admin' in data:
            errors['is_admin'] = 'You are not allowed to set admin status.'
        return errors
    
    def create_user(self, data):
        first_name = data.get('first_name' , '').strip()
        last_name = data.get('last_name' , '').strip()
        email = data.get('email' , '').strip()
        date_of_birth = data.get('date_of_birth' , '')
        password = data.get('password' , '')
        password_hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        location = data.get('location' , '').strip()
        phone_number = data.get('phone_number' , '').strip()
        user = User.objects.create(first_name=first_name , last_name=last_name , email=email , date_of_birth=date_of_birth , password=password_hashed , location=location , phone_number=phone_number , is_admin=False)
        return user
    
    def validate_login(self , data):
        errors={}
        email = data.get('email' , '').strip()
        password = data.get('password' , '')
        user = User.objects.filter(email=email).first()
        if user:
            user_password = user.password
            if bcrypt.checkpw(password.encode(), user_password.encode()):
                return {}
        errors['user'] = 'Email or password not valid'

        return errors
    
    def get_user(self, data):
        email = data.get('email' , '').strip()
        return User.objects.filter(email=email).first()

class ContactManager(models.Manager):
    def validate_message(self, data):
        errors = {}
        
        name = data.get('name', '').strip()
        if not name:
            errors['name'] = 'Name is required.'
        elif len(name) < 2:
            errors['name'] = 'Name must be at least 2 characters.'
        
        email = data.get('email', '').strip()
        if not email:
            errors['email'] = 'Email is required.'
        elif not EMAIL_REGEX.match(email):
            errors['email'] = 'Please enter a valid email address.'
        
        message = data.get('message', '').strip()
        if not message:
            errors['message'] = 'Message is required.'
        elif len(message) < 10:
            errors['message'] = 'Message must be at least 10 characters.'
        
        return errors
    
    def create_message(self, data):
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        contact = ContactMessage.objects.create(
            name=name,
            email=email,
            message=message
        )
        return contact
    
class CategoryManager(models.Manager):
    def validate_category(self, data , files=None):
        errors={}
        name = data.get('name' , '').strip()
        if not name:
            errors['name'] = 'Category name is required.'
        elif Category.objects.filter(name__iexact=name).exists():
            errors['name'] = 'Category already exists.'
        description = data.get('description' , '').strip()
        if not description:
            errors['description'] = 'Category description is required.'
        image = files.get('image') if files else None
        if not image:
            errors['image'] = 'Image is required.'
        elif not getattr(image, 'content_type', '').startswith('image/'):
            errors['image'] = 'File must be an image.'
        return errors
    
    def category_addition(self , data , files=None):
        name = data.get('name' , '').strip()
        description = data.get('description' , '').strip()
        image = files.get('image') if files else None
        category = Category.objects.create(name=name , description=description , image=image)
        return category
    
    def update_category(self, id, data, files=None):
        category = Category.objects.filter(id=id).first()
        if category:
            new_name = data.get('name')
            if new_name is None:
                new_name = category.name

            new_name = new_name.strip()
            category.name = new_name

            new_description = data.get('description')
            if new_description is None:
                new_description = category.description

            new_description = new_description.strip()
            category.description = new_description

            image = files.get('image') if files else None
            if image and getattr(image, 'content_type', '').startswith('image/'):
                category.image = image

            category.save()
        return category

    def category_deletion(self, id):
        category = Category.objects.filter(id=id).first()
        if category:
            category.delete()
            return True
        return False

class ProductManager(models.Manager):
    def validate_product(self , data , files=None):
        errors={}
        name = data.get('name' , '').strip()
        if not name:
            errors['name'] = 'Product name is required.'
        elif Product.objects.filter(name__iexact=name).exists():
            errors['name'] = 'Product already exists.'
        description = data.get('description' , '').strip()
        if not description:
            errors['description'] = 'Product description is required.'
        price = data.get('price')
        if not price:
            errors['price'] = 'Price is required.'
        elif price.count('.') > 1:
            errors['price'] = 'Invalid price.'
        elif not price.replace('.', '', 1).isdigit():
            errors['price'] = 'Invalid price.'
        else:
            decimal_price = Decimal(price)
            if decimal_price <= 0:
                errors['price'] = 'Price must be greater than 0.'

        category_id = data.get('category_id')
        if not category_id or not Category.objects.filter(id=category_id).exists():
            errors['category'] = 'Invalid category.'
        image = files.get('image') if files else None
        if not image:
            errors['image'] = 'Image is required.'
        elif not getattr(image, 'content_type', '').startswith('image/'):
            errors['image'] = 'File must be an image.'
        return errors
    
    def product_addition(self , data , files=None):
        name = data.get('name' , '').strip()
        description = data.get('description' , '').strip()
        price=Decimal(data.get('price'))
        category_id = data.get('category_id')
        category = Category.objects.get(id=category_id)
        image = files.get('image') if files else None
        product = Product.objects.create(name=name , description=description , price=price , category=category, image=image)
        return product
    
    def update_product(self, id, data, files=None):
        product = Product.objects.filter(id=id).first()
        if product:
            new_name = data.get('name')
            if new_name is None:
                new_name = product.name
            new_name = new_name.strip()
            product.name = new_name

            new_description = data.get('description')
            if new_description is None:
                new_description = product.description
            new_description = new_description.strip()
            product.description = new_description

            price = data.get('price')
            if price and price.replace('.', '', 1).isdigit():
                product.price = Decimal(price)

            category_id = data.get('category_id')
            if category_id and Category.objects.filter(id=category_id).exists():
                product.category = Category.objects.get(id=category_id)

            image = files.get('image') if files else None
            if image and getattr(image, 'content_type', '').startswith('image/'):
                product.image = image

            product.save()
        return product
    
    def product_deletion(self, id):
        product = Product.objects.filter(id=id).first()
        if product:
            product.delete()
            return True
        return False

class OrderManager(models.Manager):
    def validate_order(self, data):
        errors = {}

        custom_name = data.get('custom_name', '').strip()
        if not custom_name:
            errors['custom_name'] = 'Custom name is required.'
        event_date = data.get('event_date', '').strip()
        if event_date:
            date_parts = event_date.split('-')
            if len(date_parts) == 3 and all(part.isdigit() for part in date_parts):
                year, month, day = map(int, date_parts)
                if 1 <= month <= 12 and 1 <= day <= 31:
                    event_date_obj = datetime.date(year, month, day)
                    if event_date_obj < datetime.date.today():
                        errors['event_date'] = 'Event date must be in the future.'
                    else:
                        data['event_date_part'] = event_date_obj
                else:
                    errors['event_date'] = 'Invalid date.'
            else:
                errors['event_date'] = 'Invalid date format. Please use YYYY-MM-DD.'
        notes = data.get('notes', '').strip()
        if len(notes) > 500:
            errors['notes'] = 'Notes cannot exceed 500 characters.'

        return errors

    def create_order(self, user, data, products_qty):
        if not products_qty:
            return None
        total_price = 0
        for item in products_qty:
            product = Product.objects.get(id=item['product_id'])
            total_price += product.price * int(item['quantity'])

        custom_name=data.get('custom_name', '').strip()
        event_date=data.get('event_date_part', None)
        design_details=data.get('design_details', '').strip()
        notes=data.get('notes', '').strip()
        order = Order.objects.create(user=user , total_price=total_price , custom_name=custom_name , event_date=event_date , design_details=design_details , notes=notes)

        for item in products_qty:
            product = Product.objects.get(id=item['product_id'])
            quantity = int(item['quantity'])
            custom_details = item.get('custom_details', {})


            OrderItem.objects.create(order=order, product=product, quantity=quantity, price=product.price, custom_name=custom_details.get('custom_name', ''), event_date=custom_details.get('event_date', None), design_details=custom_details.get('design_details', ''), notes=custom_details.get('notes', ''))

        return order
    
    def recalculate_total(self, order_id):
        order = self.filter(id=order_id).first()
        if not order:
            return None

        total = 0
        for item in order.items.all():
            price = item.product.price
            quantity = item.quantity

            total += price * quantity

        order.total_price = total
        order.save()

        return order

    def update_order_status(self, order_id, new_status):
        order = self.filter(id=order_id).first()
        if not order:
            return None
        
        allowed_status = ['Pending', 'Processing', 'On the Way', 'Delivered', 'Cancelled']
        if new_status in allowed_status:
            order.status = new_status
            order.save()
            return order
        return None


class OrderItemManager(models.Manager):
    def validate_item(self, data):
        errors = {}

        product_id = data.get('product_id')
        if not product_id or not Product.objects.filter(id=product_id).exists():
            errors['product'] = 'Invalid product.'

        quantity = data.get('quantity')
        if not quantity:
            errors['quantity'] = 'Quantity is required.'
        elif not str(quantity).isdigit():
            errors['quantity'] = 'Quantity must be a number.'
        elif int(quantity) <= 0:
            errors['quantity'] = 'Quantity must be greater than 0.'

        return errors
    
    def update_quantity(self, order_id, product_id, new_quantity):
        order_item = self.filter(order_id=order_id, product_id=product_id).first()

        if not order_item:
            return None

        if new_quantity > 0:
            order_item.quantity = new_quantity
            order_item.save()
            return order_item

        order_item.delete()
        return None
    
    def remove_item(self, order_id, product_id):
        order_item = self.filter(order_id=order_id, product_id=product_id).first()

        if order_item:
            order_item.delete()
            return True

        return False

def upload_category_path(instance , filename):
    return f'categories/{filename}'

def upload_product_path(instance , filename):
    return f'products/{filename}'


class User(models.Model):
    first_name = models.CharField(max_length=45)
    last_name = models.CharField(max_length=45)
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField()
    password = models.CharField(max_length=255)
    is_admin = models.BooleanField(default=False)
    location = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=25)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = UserValidator()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    objects = ContactManager()

    def __str__(self):
        return f"Message from {self.name}"

class Category(models.Model):
    name = models.CharField(max_length=45)
    description = models.TextField()
    image = models.ImageField(upload_to=upload_category_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = CategoryManager()

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=45)
    description = models.TextField()
    price = models.DecimalField(max_digits=6 , decimal_places=2)
    image = models.ImageField(upload_to=upload_product_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category , on_delete=models.CASCADE , related_name='products')
    objects = ProductManager()

    def __str__(self):
        return self.name

status_choices = [
    ('Pending' , 'Pending'), 
    ('Processing' , 'Processing'), 
    ('On the Way' , 'On the Way'), 
    ('Delivered' , 'Delivered'), 
    ('Cancelled' , 'Cancelled'),
    ]

class Order(models.Model):
    total_price = models.DecimalField(max_digits=10 , decimal_places=2)
    order_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=45, choices=status_choices , default='Pending')
    custom_name = models.CharField(max_length=100)
    event_date = models.DateField(blank=True , null=True)
    design_details = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User , on_delete=models.CASCADE , related_name='orders')
    products = models.ManyToManyField(Product , through='OrderItem')
    objects = OrderManager()

    def __str__(self):
        return f'Order {self.id}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order , on_delete=models.CASCADE , related_name='items')
    product = models.ForeignKey(Product , on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    details = models.JSONField(blank=True, null=True)
    objects = OrderItemManager()

    def subtotal(self):
        if self.details and self.details.get('is_custom_box'):
            return self.price
        return self.price * self.quantity

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'