from rest_framework import serializers
from .models import CustomerProfile, ServiceCart

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = [
            'username', 'email', 'country_code', 'mobile', 'role',
            'profile_image', 'experience_year', 'service_skill',
            'service_km', 'document_type', 'document_file'
        ]

    def validate_username(self, value):
        if CustomerProfile.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        if CustomerProfile.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

    def validate_country_code(self, value):
        if not value.startswith('+'):
            raise serializers.ValidationError("Country code must start with '+'")
        if len(value) > 5:
            raise serializers.ValidationError("Invalid country code")
        return value
    
    def validate_mobile(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("Enter a valid 10-digit mobile number")
        if CustomerProfile.objects.filter(mobile=value).exists():
            raise serializers.ValidationError("Mobile number already exists")
        return value

    def validate_role(self, value):
        allowed_roles = ['user', 'service_provider', 'admin']
        if value not in allowed_roles:
            raise serializers.ValidationError("Invalid role")
        return value

    def validate(self, data):
        if data.get('role') == 'service_provider':
            required_fields = ['experience_year', 'service_skill', 'service_km']
            for field in required_fields:
                if not data.get(field):
                    raise serializers.ValidationError(
                        f"{field.replace('_', ' ').capitalize()} is required for service providers"
                    )
        return data


class ServiceCartSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)

    class Meta:
        model = ServiceCart
        fields = [
            'id', 'service', 'service_name', 'qty', 'num_of_tech',
            'price', 'total_price', 'status'
        ]


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = [
            "id",
            "username",
            "email",
            "country_code",
            "mobile",
            "role",
            "date_of_birth",
            "profile_image",
        ]

    def validate_role(self, value):
        """Ensure role is only 'user' for customers"""
        if value != "user":
            raise serializers.ValidationError("Role must be 'user' for customer.")
        return value