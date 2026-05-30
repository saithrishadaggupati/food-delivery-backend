from django.urls import path
from . import views

urlpatterns = [
    path('', views.restaurant_list, name='restaurant-list'),
    path('<int:pk>/', views.restaurant_detail, name='restaurant-detail'),
    path('create/', views.restaurant_create, name='restaurant-create'),
    path('<int:pk>/menu/', views.menu_item_create, name='menu-item-create'),
]