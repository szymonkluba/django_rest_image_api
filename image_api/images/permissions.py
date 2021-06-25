from rest_framework import permissions


class IsImageOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return obj.owner == request.user or request.user.is_staff or request.user.is_superuser


class AllowedSize(permissions.BasePermission):
    def has_permission(self, request, view):
        size = request.query_params.get("size", None)
        if size:
            return request.user.user_tier.plan.thumbnail_settings.filter(thumbnail_size=size).exists()
        return not size


class CanGenerateExpiringLink(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.user_tier.plan.expiring_link
