from django.shortcuts import render
import os

# DRF imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .authentication import IsAdminRole

# Django shortcuts
from django.shortcuts import get_object_or_404
from customer.models import CustomerProfile
from .models import *
from .serializers import *
from rest_framework.permissions import BasePermission

class IsRoleAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, "role", None) == "admin"

class CategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, category_id=None):
        if category_id:
            category = get_object_or_404(Category, id=category_id)
            serializer = CategorySerializer(category, context={'request': request})
            return Response({"status": 200, "message": "Category retrieved", "data": serializer.data})
        else:
            categories = Category.objects.all().order_by('-created_date')
            serializer = CategorySerializer(categories, many=True, context={'request': request})
            return Response({"status": 200, "message": "Categories fetched", "data": serializer.data})

    def post(self, request):
        print("Request user:", request.user)
        if not isinstance(request.user, CustomerProfile) or request.user.role != 'admin':
            return Response({"detail": "Unauthorized: Admin access required"}, status=401)

        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": 201, "message": "Category created", "data": serializer.data})
        return Response({"status": 400, "message": "Validation failed", "errors": serializer.errors})

    def patch(self, request, category_id):
        if not isinstance(request.user, CustomerProfile) or request.user.role != 'admin':
            return Response({"detail": "Unauthorized: Admin access required"}, status=401)

        category = get_object_or_404(Category, id=category_id)
        serializer = CategorySerializer(category, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": 200, "message": "Category updated", "data": serializer.data})
        return Response({"status": 400, "message": "Update failed", "errors": serializer.errors})

    def delete(self, request, category_id):
        if not isinstance(request.user, CustomerProfile) or request.user.role != 'admin':
            return Response({"detail": "Unauthorized: Admin access required"}, status=401)

        category = get_object_or_404(Category, id=category_id)
        category.delete()
        return Response({"status": 200, "message": "Category deleted", "data": {}})


class SubCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, subcategory_id=None):
        if subcategory_id:
            subcategory = get_object_or_404(SubCategory, id=subcategory_id)
            serializer = SubCategorySerializer(subcategory, context={'request': request})
            return Response({"status": 200, "message": "Subcategory retrieved", "data": serializer.data})
        else:
            subcategories = SubCategory.objects.all().order_by('-created_date')
            serializer = SubCategorySerializer(subcategories, many=True, context={'request': request})
            return Response({"status": 200, "message": "Subcategories fetched", "data": serializer.data})

    def post(self, request):
        if not isinstance(request.user, CustomerProfile) or request.user.role != 'admin':
            return Response({"detail": "Unauthorized: Admin access required"}, status=401)

        serializer = SubCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": 201, "message": "Subcategory created", "data": serializer.data})
        return Response({"status": 400, "message": "Validation failed", "errors": serializer.errors})

    def patch(self, request, subcategory_id):
        if not isinstance(request.user, CustomerProfile) or request.user.role != 'admin':
            return Response({"detail": "Unauthorized: Admin access required"}, status=401)

        subcategory = get_object_or_404(SubCategory, id=subcategory_id)
        serializer = SubCategorySerializer(subcategory, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": 200, "message": "Subcategory updated", "data": serializer.data})
        return Response({"status": 400, "message": "Update failed", "errors": serializer.errors})

    def delete(self, request, subcategory_id):
        if not isinstance(request.user, CustomerProfile) or request.user.role != 'admin':
            return Response({"detail": "Unauthorized: Admin access required"}, status=401)

        subcategory = get_object_or_404(SubCategory, id=subcategory_id)
        subcategory.delete()
        return Response({"status": 200, "message": "Subcategory deleted", "data": {}})


class ServiceProviderApprovalAPIView(APIView):
    permission_classes = [IsAdminRole]  # only admin can access

    def post(self, request, provider_id):
        try:
            provider = CustomerProfile.objects.get(id=provider_id, role="service_provider")
        except CustomerProfile.DoesNotExist:
            return Response({
                "status": 404,
                "message": "Service provider not found."
            }, status=404)

        action = request.data.get("action")  # approve / reject
        if action == "approve":
            provider.is_admin_verified = True
            provider.is_blocked = False  # just in case it was blocked before
            provider.save()
            return Response({
                "status": 200,
                "message": "Service provider approved successfully."
            })

        elif action == "reject":
            provider.is_blocked = True
            provider.blocked_reason = request.data.get("reason", "Rejected by admin")
            provider.is_admin_verified = False
            provider.save()
            return Response({
                "status": 200,
                "message": "Service provider rejected."
            })

        return Response({
            "status": 400,
            "message": "Invalid action. Use 'approve' or 'reject'."
        }, status=400)
