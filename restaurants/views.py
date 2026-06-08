from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.measure import D
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.cache import cache
from django.conf import settings

from core.permissions import IsRestaurantOwner
from .models import Restaurant, MenuItem
from .serializers import RestaurantSerializer, MenuItemSerializer

RESTAURANT_LIST_CACHE_KEY = 'restaurant_list_page_{page}_size_{size}'
CACHE_TTL = 60 * 15  # 15 minutes


@api_view(['GET'])
@permission_classes([AllowAny])
def restaurant_list(request):
    page = request.query_params.get('page', 1)
    page_size = 10
    cache_key = RESTAURANT_LIST_CACHE_KEY.format(page=page, size=page_size)

    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    restaurants = Restaurant.objects.filter(
        is_active=True
    ).select_related('owner').prefetch_related('menu_items')

    paginator = PageNumberPagination()
    paginator.page_size = page_size
    result_page = paginator.paginate_queryset(restaurants, request)
    serializer = RestaurantSerializer(result_page, many=True)

    response = paginator.get_paginated_response(serializer.data)
    cache.set(cache_key, response.data, CACHE_TTL)
    return response


@api_view(['GET'])
@permission_classes([AllowAny])
def restaurant_detail(request, pk):
    try:
        restaurant = Restaurant.objects.select_related(
            'owner'
        ).prefetch_related('menu_items').get(pk=pk, is_active=True)
    except Restaurant.DoesNotExist:
        return Response({'error': 'Restaurant not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = RestaurantSerializer(restaurant)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsRestaurantOwner])
def restaurant_create(request):
    serializer = RestaurantSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(owner=request.user)
        cache.delete_pattern('restaurant_list_page_*')
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsRestaurantOwner])
def menu_item_create(request, pk):
    try:
        restaurant = Restaurant.objects.get(pk=pk, owner=request.user)
    except Restaurant.DoesNotExist:
        return Response(
            {'error': 'Restaurant not found or not authorized'},
            status=status.HTTP_404_NOT_FOUND
        )

    serializer = MenuItemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(restaurant=restaurant)
        cache.delete_pattern('restaurant_list_page_*')
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET'])
@permission_classes([AllowAny])
def nearby_restaurants(request):
    lat = request.query_params.get('lat')
    lng = request.query_params.get('lng')
    radius_km = float(request.query_params.get('radius', 5))

    if not lat or not lng:
        return Response(
            {'error': 'lat and lng query parameters are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user_location = Point(float(lng), float(lat), srid=4326)
    except (ValueError, TypeError):
        return Response(
            {'error': 'Invalid lat or lng values'},
            status=status.HTTP_400_BAD_REQUEST
        )

    restaurants = Restaurant.objects.filter(
        is_active=True,
        location__isnull=False,
        location__dwithin=(user_location, D(km=radius_km))
    ).annotate(
        distance=Distance('location', user_location)
    ).order_by('distance').select_related('owner').prefetch_related('menu_items')

    serializer = RestaurantSerializer(restaurants, many=True)
    return Response({
        'count': restaurants.count(),
        'radius_km': radius_km,
        'results': serializer.data
    })