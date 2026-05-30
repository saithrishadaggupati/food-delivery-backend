from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.core.cache import cache
from django.conf import settings
from .models import Restaurant, MenuItem
from .serializers import RestaurantSerializer, MenuItemSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def restaurant_list(request):
    cache_key = 'restaurant_list'
    cached_data = cache.get(cache_key)

    if cached_data:
        return Response(cached_data)

    restaurants = Restaurant.objects.filter(is_active=True)
    serializer = RestaurantSerializer(restaurants, many=True)
    cache.set(cache_key, serializer.data, settings.CACHE_TTL)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def restaurant_detail(request, pk):
    try:
        restaurant = Restaurant.objects.get(pk=pk, is_active=True)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restaurant not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = RestaurantSerializer(restaurant)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def restaurant_create(request):
    if request.user.role != 'restaurant_owner':
        return Response({'error': 'Only restaurant owners can create restaurants'}, status=status.HTTP_403_FORBIDDEN)
    serializer = RestaurantSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def menu_item_create(request, pk):
    try:
        restaurant = Restaurant.objects.get(pk=pk, owner=request.user)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restaurant not found or not authorized'}, status=status.HTTP_404_NOT_FOUND)
    serializer = MenuItemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(restaurant=restaurant)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)