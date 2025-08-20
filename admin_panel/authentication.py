from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from customer.models import CustomerProfile
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework.permissions import BasePermission

class CustomerJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user_id = validated_token.get("user_id")
        if user_id is None:
            raise AuthenticationFailed("Token contained no recognizable user identification")

        try:
            user = CustomerProfile.objects.get(id=user_id)
            user.is_authenticated = True
            return user
        except CustomerProfile.DoesNotExist:
            raise AuthenticationFailed("User not found")
        except (TokenError, InvalidToken):
            raise AuthenticationFailed("Token is invalid or expired")


class IsAdminRole(BasePermission):
    """
    Custom permission to allow only users with role='admin'.
    """

    def has_permission(self, request, view):
        return bool(request.user and getattr(request.user, "role", None) == "admin")