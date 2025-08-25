from django.shortcuts import render
import os

# DRF imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .authentication import IsAdminRole

# Django shortcuts
from django.shortcuts import get_object_or_404
from customer.models import CustomerProfile, Address, PendingProfileUpdate, PendingBankDetailUpdate
from customer.serializers import CustomerProfileSerializer
from .models import *
from .serializers import *
from rest_framework.permissions import BasePermission
from service.serializers import BankDetailSerializer

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

    def get(self, request, category_id=None):
        if not category_id:
            return Response(
                {"status": 400, "message": "Category ID is required"},
                status=400
            )

        subcategories = SubCategory.objects.filter(category_id=category_id).order_by('-created_date')

        if not subcategories.exists():
            return Response(
                {"status": 404, "message": "No subcategories found for this category"},
                status=404
            )

        if hasattr(request.user, "role") and request.user.role == "admin":
            serializer_class = SubCategorySerializer
        else:
            serializer_class = SubCategoryPublicSerializer

        serializer = serializer_class(subcategories, many=True, context={'request': request})
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


class SubCategoryItemView(APIView):
    permission_classes = [IsAuthenticated]

    # Get all items for a subcategory (allowed for all users)
    def get(self, request, subcategory_id):
        items = SubCategoryItem.objects.filter(subcategory_id=subcategory_id)
        if not items.exists():
            return Response(
                {"status": 404, "message": "No items found for this subcategory"},
                status=404
            )

        serializer = SubCategoryItemSerializer(items, many=True)
        return Response({"status": 200, "message": "Items fetched", "data": serializer.data})

    # Create new item inside a subcategory (only admin)
    def post(self, request, subcategory_id):
        if request.user.role != 'admin':
            return Response(
                {"status": 403, "message": "Only admin can create items"},
                status=403
            )

        data = request.data.copy()
        data['subcategory'] = subcategory_id  # force bind to this subcategory

        serializer = SubCategoryItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": 201, "message": "Item created", "data": serializer.data})
        return Response({"status": 400, "message": "Validation failed", "errors": serializer.errors})

    # Update an existing item (only admin)
    def patch(self, request, item_id):
        if request.user.role != 'admin':
            return Response(
                {"status": 403, "message": "Only admin can update items"},
                status=403
            )

        item = get_object_or_404(SubCategoryItem, id=item_id)

        # prevent updating subcategory
        data = request.data.copy()
        data.pop("subcategory", None)

        serializer = SubCategoryItemSerializer(item, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"status": 200, "message": "Item updated", "data": serializer.data})
        return Response({"status": 400, "message": "Update failed", "errors": serializer.errors})

    # Delete an item (only admin)
    def delete(self, request, item_id):
        if request.user.role != 'admin':
            return Response(
                {"status": 403, "message": "Only admin can delete items"},
                status=403
            )

        item = get_object_or_404(SubCategoryItem, id=item_id)
        item.delete()
        return Response({"status": 200, "message": "Item deleted", "data": {}})


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


class PendingProfileApprovalView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        """Fetch all pending profile update requests"""
        pending_requests = PendingProfileUpdate.objects.filter(reviewed=False)
        serializer = PendingProfileUpdateSerializer(pending_requests, many=True)
        return Response({"status": 200, "data": serializer.data})

    def patch(self, request, pk):
        """Approve or Reject a pending profile update"""
        pending = get_object_or_404(PendingProfileUpdate, id=pk, reviewed=False)
        action = request.data.get("action")

        if action == "approve":
            data = pending.data
            profile = pending.profile

            # ✅ Update main profile
            from service.serializers import ServiceProviderProfileSerializer, AddressSerializer
            serializer = ServiceProviderProfileSerializer(profile, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # ✅ Handle addresses
            addresses_data = data.get("addresses", [])
            for addr in addresses_data:
                addr_id = addr.get("id")
                if addr_id:
                    try:
                        address_instance = Address.objects.get(id=addr_id, user=profile)
                        addr_serializer = AddressSerializer(address_instance, data=addr, partial=True)
                        addr_serializer.is_valid(raise_exception=True)
                        addr_serializer.save()
                    except Address.DoesNotExist:
                        continue
                else:
                    # FIX: set user via save()
                    addr_serializer = AddressSerializer(data=addr)
                    addr_serializer.is_valid(raise_exception=True)
                    addr_serializer.save(user=profile)

            pending.approved = True
            pending.reviewed = True
            pending.save()

            return Response({"status": 200, "message": "Profile update approved and applied"})

        elif action == "reject":
            pending.reviewed = True
            pending.approved = False
            pending.save()
            return Response({"status": 200, "message": "Profile update request rejected"})

        return Response({"status": 400, "message": "Invalid action"})
    

class PendingBankDetailApprovalView(APIView):
    permission_classes = [IsAdminRole]

    def get(self, request):
        """Fetch all pending bank detail update requests"""
        pending = PendingBankDetailUpdate.objects.filter(reviewed=False)
        serializer = PendingBankDetailUpdateSerializer(pending, many=True)
        return Response({"status": 200, "data": serializer.data})

    def patch(self, request, pk):
        """Approve or reject a pending bank detail update"""
        pending = get_object_or_404(PendingBankDetailUpdate, id=pk, reviewed=False)
        action = request.data.get("action")

        if action == "approve":
            data = pending.data
            bank_detail = pending.bank_detail

            serializer = BankDetailSerializer(bank_detail, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            pending.approved = True
            pending.reviewed = True
            pending.save()

            return Response({"status": 200, "message": "Bank detail update approved and applied"})

        elif action == "reject":
            pending.reviewed = True
            pending.approved = False
            pending.save()
            return Response({"status": 200, "message": "Bank detail update request rejected"})

        return Response({"status": 400, "message": "Invalid action"})
