from django.urls import path
from . import views

urlpatterns = [
    path('place/', views.place_order, name='place-order'),
    path('my-orders/', views.my_orders, name='my-orders'),
    path('<int:pk>/status/', views.update_order_status, name='update-order-status'),
]