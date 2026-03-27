from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_order_confirmation(order):
    """Send order confirmation email"""
    subject = f'Order Confirmation - Order #{order.id}'
    

    text_content = f'''
    Thank you for your order!
    
    Order ID: {order.id}
    Total: {order.total_price} ₪
    
    We'll notify you when your order ships.
    '''
    
    # HTML version using template
    html_content = render_to_string('emails/order_confirmation.html', {
        'order': order,
        'user': order.user,
    })
    
    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.user.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()

def send_welcome_email(user):
    """Send welcome email to new users"""
    send_mail(
        subject='Welcome to Guilt Bites!',
        message='Thanks for joining Guilt Bites. Start shopping now!',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )

def send_password_reset(user, reset_url):
    """Send password reset email"""
    html_content = render_to_string('emails/password_reset.html', {
        'user': user,
        'reset_url': reset_url,
    })
    
    msg = EmailMultiAlternatives(
        subject='Password Reset Request',
        body=f'Click here to reset: {reset_url}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    msg.attach_alternative(html_content, "text/html")
    msg.send()