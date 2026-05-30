from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # Every food delivery app needs phone number
    phone = models.CharField(max_length=15, blank=True)
    
    # Are they a customer or a restaurant owner?
    ROLE_CHOICES = (
        ('customer', 'Customer'),
        ('restaurant_owner', 'Restaurant Owner'),
        ('delivery_agent', 'Delivery Agent'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')
    
    # Where to deliver?
    address = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.username} ({self.role})"