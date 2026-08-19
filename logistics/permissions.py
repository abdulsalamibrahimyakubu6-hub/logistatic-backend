from rest_framework import permissions
from .models import User


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == User.Role.ADMIN

class IsDriver(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.User.is_authenticated and request.user.role == User.Role.DRIVER

class IsShipmentOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view, obj):
        if request.user.role == User.Role.ADMIN:
            return True
        return obj.customer == request.user or obj.driver == request.user

    
