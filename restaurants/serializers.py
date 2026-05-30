from rest_framework import serializers
from .models import Restaurant, MenuItem


class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'name', 'description', 'price', 'category', 'is_available', 'created_at']


class RestaurantSerializer(serializers.ModelSerializer):
    menu_items = MenuItemSerializer(many=True, read_only=True)
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'description', 'address', 'phone', 'email',
                  'cuisine_type', 'is_active', 'opening_time', 'closing_time',
                  'owner_username', 'menu_items', 'created_at']