from rest_framework import serializers
from customer.models import CustomerProfile, Address

class ServiceRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = [
            "username", "email", "country_code", "mobile", "role",
            "profile_image", "experience_year", "service_skill", "service_km",
            "document_type", "document_file",
            "is_gov_verified", "is_police_verified", "is_admin_verified", "is_verified",
            "categories"
        ]
        read_only_fields = ["is_verified", "is_admin_verified"]

    def validate_role(self, value):
        if value != "electrician":
            raise serializers.ValidationError("Role must be electrician for this API.")
        return value

    def validate_email(self, value):
        if CustomerProfile.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already registered.")
        return value

    def validate_mobile(self, value):
        if CustomerProfile.objects.filter(mobile=value).exists():
            raise serializers.ValidationError("Mobile number is already registered.")
        return value


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"

class ServiceProfileSerializer(serializers.ModelSerializer):
    addresses = AddressSerializer(many=True, read_only=True)

    class Meta:
        model = CustomerProfile
        fields = "__all__" 