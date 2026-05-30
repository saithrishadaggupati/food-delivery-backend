from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Order, OrderItem
from .serializers import OrderSerializer
from restaurants.models import Restaurant, MenuItem


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def place_order(request):
    # Only customers can place orders
    if request.user.role != 'customer':
        return Response({'error': 'Only customers can place orders'}, status=status.HTTP_403_FORBIDDEN)

    restaurant_id = request.data.get('restaurant_id')
    delivery_address = request.data.get('delivery_address')
    items = request.data.get('items', [])

    try:
        restaurant = Restaurant.objects.get(pk=restaurant_id, is_active=True)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restaurant not found'}, status=status.HTTP_404_NOT_FOUND)

    if not items:
        return Response({'error': 'No items in order'}, status=status.HTTP_400_BAD_REQUEST)

    order = Order.objects.create(
        customer=request.user,
        restaurant=restaurant,
        delivery_address=delivery_address,
        total_amount=0
    )

    total = 0
    for item in items:
        try:
            menu_item = MenuItem.objects.get(pk=item['menu_item_id'], restaurant=restaurant)
        except MenuItem.DoesNotExist:
            order.delete()
            return Response({'error': f'Menu item {item["menu_item_id"]} not found'}, status=status.HTTP_404_NOT_FOUND)

        quantity = item.get('quantity', 1)
        price = menu_item.price
        OrderItem.objects.create(order=order, menu_item=menu_item, quantity=quantity, price=price)
        total += price * quantity

    order.total_amount = total
    order.save()

    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_orders(request):
    # Customers see their own orders
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_order_status(request, pk):
    # Only restaurant owner can update status
    try:
        order = Order.objects.get(pk=pk, restaurant__owner=request.user)
    except Order.DoesNotExist:
        return Response({'error': 'Order not found or not authorized'}, status=status.HTTP_404_NOT_FOUND)

    new_status = request.data.get('status')
    valid_statuses = ['confirmed', 'preparing', 'out_for_delivery', 'delivered', 'cancelled']
    if new_status not in valid_statuses:
        return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)

    order.status = new_status
    order.save()
    return Response(OrderSerializer(order).data)