from rest_framework.permissions import BasePermission


class IsCustomer(BasePermission):
    """Allow access only to users with the customer role."""
    message = 'Only customers can perform this action.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'customer')


class IsRestaurantOwner(BasePermission):
    """Allow access only to users with the restaurant_owner role."""
    message = 'Only restaurant owners can perform this action.'

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'restaurant_owner')


class IsOwnerOfRestaurant(BasePermission):
    """Object-level permission — only the owner of the specific restaurant can edit it."""
    message = 'You do not own this restaurant.'

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user