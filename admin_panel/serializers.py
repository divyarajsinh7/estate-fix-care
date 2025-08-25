from rest_framework import serializers
from .models import *
from customer.models import PendingProfileUpdate, PendingBankDetailUpdate
import os

class CategorySerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = Category
        fields = ['id', 'category_name', 'image', 'image_url', 'created_date', 'updated_date']
    
    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None
    
    def validate_image(self, value):
        """
        Validate file type for uploaded image.
        Allowed: svg, png, jpg, jpeg
        """
        ext = os.path.splitext(value.name)[1].lower()  # Get file extension
        allowed_extensions = ['.svg', '.png', '.jpg', '.jpeg']
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f"Unsupported file format. Allowed formats are: {', '.join(allowed_extensions)}"
            )
        return value


class SubCategoryPublicSerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = SubCategory
        fields = ['id', 'name', 'cover_image_url']

    def get_cover_image_url(self, obj):
        request = self.context.get('request')
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        elif obj.cover_image:
            return obj.cover_image.url
        return None


class SubCategorySerializer(serializers.ModelSerializer):
    cover_image_url = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = SubCategory
        fields = [
            'id', 'name', 'category', 'description', 'cover_image', 'image',
            'section', 'steps', 'faqs', 'price', 'created_date', 'updated_date',
            'cover_image_url', 'image_url'
        ]

    def get_cover_image_url(self, obj):
        request = self.context.get('request')
        if obj.cover_image and request:
            return request.build_absolute_uri(obj.cover_image.url)
        elif obj.cover_image:
            return obj.cover_image.url
        return None

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None


class PendingProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingProfileUpdate
        fields = "__all__"


class PendingBankDetailUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PendingBankDetailUpdate
        fields = ["id", "bank_detail", "data", "created_at", "approved", "reviewed"]


class SubCategoryItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategoryItem
        fields = ['id', 'subcategory', 'step_no', 'title', 'description', 'created_date', 'updated_date']
        read_only_fields = ['id', 'created_date', 'updated_date']