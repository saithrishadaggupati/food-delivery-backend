from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_order_confirmation(order_id, customer_email, restaurant_name, total_amount):
    """Send order confirmation email to customer in the background."""
    send_mail(
        subject=f'Order #{order_id} Confirmed',
        message=(
            f'Your order from {restaurant_name} has been placed successfully.\n'
            f'Total: ₹{total_amount}\n'
            f'We will notify you when your order is out for delivery.'
        ),
        from_email='noreply@fooddelivery.com',
        recipient_list=[customer_email],
        fail_silently=True,
    )
    return f'Confirmation sent for order {order_id}'


@shared_task
def notify_restaurant(order_id, restaurant_name, total_amount, item_count):
    """Notify restaurant of new order in the background."""
    # In production this would send a push notification or SMS
    # For now we log it — easily extensible
    print(f'[ORDER ALERT] {restaurant_name} — Order #{order_id} | {item_count} items | ₹{total_amount}')
    return f'Restaurant notified for order {order_id}'