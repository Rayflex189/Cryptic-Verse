from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Admin

class IsAdminUserToken(permissions.BasePermission):
    def has_permission(self, request, view):
        auth = JWTAuthentication()
        try:
            header = auth.get_header(request)
            if header is None:
                return False
            raw_token = auth.get_raw_token(header)
            validated_token = auth.get_validated_token(raw_token)
            
            if validated_token.get('is_admin') is True:
                admin_id = validated_token.get('admin_id')
                request.admin_user = Admin.objects.get(id=admin_id)
                return True
        except Exception:
            pass
        return False
