from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        # 1. Дозволяємо всім (навіть анонімам) безпечні методи (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True

        # 2. Для POST, PUT, DELETE перевіряємо, чи юзер залогінений І чи він Staff
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_staff
        )