from .tasks import send_order_confirmation, notify_restaurant
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db import transaction
from django.core.cache import cache

from core.permissions import IsCustomer, IsRestaurantOwner
from .models import Order, OrderItem
from .serializers import OrderSerializer
from restaurants.models import Restaurant, MenuItem

IDEMPOTENCY_TTL = 60 * 60 * 24  # 24 hours


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsCustomer])
def place_order(request):
    idempotency_key = request.headers.get('Idempotency-Key')
    if idempotency_key:
        cache_key = f'idempotency_{request.user.id}_{idempotency_key}'
        cached_response = cache.get(cache_key)
        if cached_response:
            return Response(cached_response, status=status.HTTP_200_OK)

    restaurant_id = request.data.get('restaurant_id')
    delivery_address = request.data.get('delivery_address')
    items = request.data.get('items', [])

    try:
        restaurant = Restaurant.objects.get(pk=restaurant_id, is_active=True)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restaurant not found'}, status=status.HTTP_404_NOT_FOUND)

    if not items:
        return Response({'error': 'No items in order'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        with transaction.atomic():
            order = Order.objects.create(
                customer=request.user,
                restaurant=restaurant,
                delivery_address=delivery_address,
                total_amount=0
            )

            total = 0
            order_items = []

            for item in items:
                try:
                    menu_item = MenuItem.objects.get(
                        pk=item['menu_item_id'],
                        restaurant=restaurant,
                        is_available=True
                    )
                except MenuItem.DoesNotExist:
                    raise ValueError(f"Menu item {item['menu_item_id']} not found or unavailable")

                quantity = item.get('quantity', 1)
                price = menu_item.price
                order_items.append(
                    OrderItem(order=order, menu_item=menu_item, quantity=quantity, price=price)
                )
                total += price * quantity

            OrderItem.objects.bulk_create(order_items)
            order.total_amount = total
            order.save()

    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    response_data = OrderSerializer(order).data

    if idempotency_key:
        cache.set(cache_key, response_data, IDEMPOTENCY_TTL)

    # Fire background tasks — non-blocking
    send_order_confirmation.delay(
        order_id=order.id,
        customer_email=request.user.email,
        restaurant_name=restaurant.name,
        total_amount=str(order.total_amount)
    )
    notify_restaurant.delay(
        order_id=order.id,
        restaurant_name=restaurant.name,
        total_amount=str(order.total_amount),
        item_count=len(order_items)
    )

    return Response(response_data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsCustomer])
def my_orders(request):
    orders = Order.objects.filter(
        customer=request.user
    ).select_related(
        'restaurant'
    ).prefetch_related(
        'items__menu_item'
    ).order_by('-created_at')

    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsRestaurantOwner])
def update_order_status(request, pk):
    try:
        order = Order.objects.select_related('restaurant').get(
            pk=pk, restaurant__owner=request.user
        )
    except Order.DoesNotExist:
        return Response({'error': 'Order not found or not authorized'}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get('status')
    valid_statuses = ['confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    order.status = new_status
    order.save()
    return Response(OrderSerializer(order).data)