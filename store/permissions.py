from rest_framework.permissions import BasePermission,IsAuthenticated,SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)
    

# Custom permission to allow users to manage their own profile
class IsSelfOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow admin or if the user is retrieving/updating their own profile
        return request.user.is_staff or obj.user == request.user
    

class IsCartOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow if user is the cart owner
        return obj.user == request.user