from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import *
from django.shortcuts import get_object_or_404
from .serializers import *
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
import re
from user_agents import parse
from rest_framework.permissions import IsAuthenticated
from admin_panel.models import SubCategory
import razorpay
from django.conf import settings
from .utils import create_booking_notifications
from django.db import transaction
from decimal import Decimal


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            mobile = serializer.validated_data['mobile']
            email = serializer.validated_data['email']
            username = serializer.validated_data['username']
            role = serializer.validated_data['role']

            # Get or create profile
            customer, created = CustomerProfile.objects.get_or_create(
                mobile=mobile,
                defaults={
                    "username": username,
                    "email": email,
                    "role": role
                }
            )

            # Create OTP
            otp = customer.create_otp()

            return Response({
                "status": 200,
                "message": "OTP sent successfully",
                "otp": otp  # ⚠️ remove in production
            })

        return Response({
            "status": 400,
            "message": "Invalid data",
            "errors": serializer.errors
        }, status=400)
    

class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        mobile = request.data.get("mobile")
        otp_entered = request.data.get("otp")

        try:
            customer = CustomerProfile.objects.get(mobile=mobile)
        except CustomerProfile.DoesNotExist:
            return Response({"status": 404, "message": "User not found"}, status=404)

        if not customer.is_otp_valid():
            return Response({"status": 400, "message": "OTP expired"}, status=400)

        if customer.otp_verify(otp_entered):
            customer.is_verified = True
            customer.save()
            return Response({"status": 200, "message": "OTP verified successfully"})
        else:
            return Response({"status": 400, "message": "Invalid OTP"}, status=400)
        

class VerifyOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        country_code = request.data.get("country_code")
        mobile = request.data.get("mobile")
        otp_entered = request.data.get("otp")

        if not country_code or not mobile or not otp_entered:
            return Response({"status": 400, "message": "country_code, mobile, and otp are required"}, status=400)

        try:
            customer = CustomerProfile.objects.get(country_code=country_code, mobile=mobile)
        except CustomerProfile.DoesNotExist:
            return Response({"status": 404, "message": "User not found"}, status=404)

        if not customer.is_otp_valid():
            return Response({"status": 400, "message": "OTP expired"}, status=400)

        if customer.otp_verify(otp_entered):
            customer.is_verified = True
            customer.save()
            return Response({"status": 200, "message": "OTP verified successfully"})
        else:
            return Response({"status": 400, "message": "Invalid OTP"}, status=400)


class GenerateOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        country_code = request.data.get("country_code")
        mobile = request.data.get("mobile")

        if not country_code or not mobile:
            return Response({"status": 400, "message": "country_code and mobile are required"}, status=400)

        try:
            customer = CustomerProfile.objects.get(country_code=country_code, mobile=mobile)
        except CustomerProfile.DoesNotExist:
            return Response({"status": 404, "message": "User not found"}, status=404)

        # Check OTP validity
        if customer.is_otp_valid():
            return Response({
                "status": 200,
                "message": "OTP already sent and still valid",
                "otp": customer.otp
            })

        # Generate new OTP
        otp = customer.create_otp()

        return Response({
            "status": 200,
            "message": "New OTP generated successfully",
            "otp": otp
        })


class LoginSendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        country_code = request.data.get("country_code")
        mobile = request.data.get("mobile")

        # Validate country code
        if not country_code or not country_code.startswith("+") or not country_code[1:].isdigit():
            return Response({"status": 400, "message": "Invalid or missing country code"}, status=400)

        # Validate mobile
        if not mobile or not re.fullmatch(r"\d{10}", mobile):
            return Response({"status": 400, "message": "Invalid or missing mobile number (must be 10 digits)"}, status=400)

        # Check if user exists
        try:
            user = CustomerProfile.objects.get(country_code=country_code, mobile=mobile)
        except CustomerProfile.DoesNotExist:
            return Response({"status": 404, "message": "User not found"}, status=404)

        # Check if OTP is still valid
        if user.is_otp_valid():
            return Response({
                "status": 200,
                "message": "OTP already sent and still valid",
                "otp": user.otp  # ⚠️ remove in production
            }, status=200)

        # Generate new OTP using model method
        generated_otp = user.create_otp()

        print(f"[DEBUG] OTP for {country_code}{mobile}: {generated_otp}")

        return Response({
            "status": 200,
            "message": "OTP sent to your mobile",
            "otp": generated_otp  # ⚠️ remove in production
        }, status=200)
    

class LoginVerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        country_code = request.data.get("country_code")
        mobile = request.data.get("mobile")
        otp_entered = request.data.get("otp")

        if not country_code or not mobile or not otp_entered:
            return Response({"status": 400, "message": "country_code, mobile, and otp are required"}, status=400)

        try:
            user = CustomerProfile.objects.get(country_code=country_code, mobile=mobile)
        except CustomerProfile.DoesNotExist:
            return Response({"status": 404, "message": "User not found"}, status=404)

        # Check if OTP is valid (not expired)
        if not user.is_otp_valid():
            return Response({"status": 400, "message": "OTP expired"}, status=400)

        # Verify OTP match
        if not user.otp_verify(otp_entered):
            return Response({"status": 400, "message": "Invalid OTP"}, status=400)

        # OTP verified → clear OTP fields
        user.otp = None
        user.otp_created_at = None
        user.save()

        # Device Detection
        user_agent_str = request.META.get("HTTP_USER_AGENT", "")
        user_agent = parse(user_agent_str)
        device_type = "PC"
        if user_agent.is_mobile:
            device_type = "Mobile"
        elif user_agent.is_tablet:
            device_type = "Tablet"
        elif user_agent.is_bot:
            device_type = "Bot"

        os_name = user_agent.os.family
        browser = user_agent.browser.family

        # Save login log
        SystemLog.objects.create(
            type="login",
            performed_by=user,
            remark=f"Login from {device_type} using {browser} on {os_name}"
        )

        # Generate JWT tokens directly
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        return Response({
            "status": 200,
            "message": "Login success",
            "data": {
                "user_id": user.id,
                "country_code": user.country_code,
                "mobile": user.mobile,
                "access_token": str(access),
                "refresh_token": str(refresh),
                "device_type": device_type,
                "os": os_name,
                "browser": browser
            }
        }, status=200)
    

class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get all items in the user's cart"""
        user = request.user
        cart = Cart.objects.filter(user=user).first()

        if not cart:
            return Response({
                "status": 200,
                "message": "Cart is empty",
                "data": {"items": [], "total": 0}
            }, status=200)

        items = ServiceCart.objects.filter(cart=cart)
        total = sum(item.total_price for item in items)
        data = ServiceCartSerializer(items, many=True).data

        return Response({
            "status": 200,
            "message": "Cart fetched",
            "data": {"items": data, "total": total}
        }, status=200)

    def post(self, request):
        """Add item to cart (or update if exists)"""
        service_id = request.data.get("service")
        qty = int(request.data.get("qty", 1))
        num_of_tech = int(request.data.get("num_of_tech", 1))

        user = request.user
        service = get_object_or_404(SubCategory, id=service_id)
        price = float(service.price)

        cart, _ = Cart.objects.get_or_create(user=user)
        item, created = ServiceCart.objects.get_or_create(cart=cart, service=service)

        item.qty = qty
        item.num_of_tech = num_of_tech
        item.price = price
        item.total_price = qty * num_of_tech * price
        item.save()

        return Response({
            "status": 201,
            "message": "Item added to cart" if created else "Cart updated",
            "data": ServiceCartSerializer(item).data
        }, status=201 if created else 200)

    def patch(self, request, item_id=None):
        """Update cart item (qty or num_of_tech)"""
        user = request.user
        item = get_object_or_404(ServiceCart, id=item_id)

        if item.cart.user != user:
            return Response({
                "status": 403,
                "message": "You do not have permission to update this item"
            }, status=403)

        qty = request.data.get("qty", item.qty)
        num_of_tech = request.data.get("num_of_tech", item.num_of_tech)

        item.qty = int(qty)
        item.num_of_tech = int(num_of_tech)
        item.total_price = item.qty * item.num_of_tech * item.price
        item.save()

        return Response({
            "status": 200,
            "message": "Cart item updated",
            "data": ServiceCartSerializer(item).data
        }, status=200)

    def delete(self, request, item_id=None):
        """Delete one item or clear entire cart"""
        user = request.user

        if item_id:  # Delete a single cart item
            item = get_object_or_404(ServiceCart, id=item_id)
            if item.cart.user != user:
                return Response({
                    "status": 403,
                    "message": "You do not have permission to delete this item"
                }, status=403)
            item.delete()
            return Response({
                "status": 200,
                "message": "Cart item removed"
            }, status=200)

        # No item_id → clear entire cart
        cart = Cart.objects.filter(user=user).first()
        if cart:
            cart.services.all().delete()

        return Response({
            "status": 200,
            "message": "Cart cleared"
        }, status=200)


class GeneratePaymentOTPView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # ✅ Generate 6-digit OTP
        otp = str(random.randint(100000, 999999))

        # ✅ Create empty booking with OTP OR store in session
        booking = ServiceBook.objects.create(
            user=user,
            service=None,  # service will be attached later at checkout
            service_start_otp=otp,
            otp_generated_at=timezone.now(),
            status="pending"
        )

        # TODO: Send OTP via SMS/Email (integrate Twilio, AWS SNS, or SMTP)

        return Response({
            "status": 200,
            "message": "OTP generated successfully",
            "booking_id": booking.id,
            "otp": otp  # ❌
        })
    

class RazorpayCheckoutView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        otp = request.data.get("otp")
        booking_id = request.data.get("booking_id")

        if not otp or not booking_id:
            return Response({"status": 400, "message": "OTP & booking_id required"}, status=400)

        try:
            booking_obj = ServiceBook.objects.get(id=booking_id, user=user, service_start_otp=otp)
        except ServiceBook.DoesNotExist:
            return Response({"status": 400, "message": "Invalid OTP"}, status=400)

        # ✅ OTP verified
        booking_obj.otp_verified_at = timezone.now()
        booking_obj.otp_verified_by = user
        booking_obj.save()

        cart = Cart.objects.filter(user=user).first()
        if not cart or not cart.services.exists():
            return Response({"status": 400, "message": "Cart is empty"}, status=400)

        default_address = Address.objects.filter(user=user, is_default=True).first()
        if not default_address:
            return Response({"status": 400, "message": "No default address found"}, status=400)

        bookings, total_amount, notifications_list = [], Decimal("0.0"), []

        for item in cart.services.all():
            electrician = None  
            booking_status = 'assign' if electrician else 'pending'

            booking = ServiceBook.objects.create(
                user=user,
                service=item.service,
                technician_required=item.num_of_tech,
                status=booking_status,
                is_scheduled=False,
                service_start_otp=otp,
                otp_generated_at=booking_obj.otp_generated_at,
                assigned_technician=electrician
            )

            total_amount += Decimal(str(item.total_price))

            if electrician:
                booking_notifications = create_booking_notifications(
                    user_profile=booking.user,
                    electrician_profile=booking.assigned_technician,
                    booking=booking
                )
                notifications_list.append(booking_notifications)

            bookings.append({
                "id": booking.id,
                "service": item.service.name,
                "assigned_technician": electrician.username if electrician else None,
                "status": booking_status,
                "scheduled_time": booking.scheduled_time if hasattr(booking, "scheduled_time") else None,
                "created_at": booking.created_at if hasattr(booking, "created_at") else timezone.now()
            })

        # ✅ Razorpay order
        razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        razorpay_order = razorpay_client.order.create({
            "amount": int(total_amount * 100),
            "currency": "INR",
            "payment_capture": "1"
        })

        ServiceBook.objects.filter(id__in=[b["id"] for b in bookings]).update(
            quatation_amt=total_amount,
            comment=f"Razorpay Order ID: {razorpay_order['id']}"
        )

        cart.services.all().delete()

        # ✅ Build full response
        response_data = {
            "status": 200,
            "message": "Checkout successful",
            "data": {
                "payment": {
                    "total_amount": str(total_amount),
                    "currency": "INR",
                    "razorpay_order_id": razorpay_order["id"],
                    "payment_status": razorpay_order.get("status", "created"), 
                    "payment_method": None
                },
                "bookings": bookings,
                "customer": {
                    "id": user.id,
                    "name": user.username,
                    "email": user.email,
                    "phone_number": getattr(user, "phone_number", None)
                },
                "address": {
                    "label": default_address.label,
                    "address": default_address.address,
                    "city": default_address.city,
                    "state": default_address.state,
                    "pincode": default_address.pincode,
                    "latitude": getattr(default_address, "latitude", None),
                    "longitude": getattr(default_address, "longitude", None),
                },
                "notifications": notifications_list,
                "support": {
                    "contact_number": "+91-1800-123-456",
                    "email": "support@example.com"
                }
            }
        }

        return Response(response_data)


    

# class VerifyPaymentView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         razorpay_payment_id = request.data.get("razorpay_payment_id")
#         razorpay_order_id = request.data.get("razorpay_order_id")
#         razorpay_signature = request.data.get("razorpay_signature")

#         if not (razorpay_payment_id and razorpay_order_id and razorpay_signature):
#             return Response({"status": 400, "message": "Missing payment details"}, status=400)

#         try:
#             # ✅ Verify payment signature
#             params_dict = {
#                 "razorpay_order_id": razorpay_order_id,
#                 "razorpay_payment_id": razorpay_payment_id,
#                 "razorpay_signature": razorpay_signature
#             }
#             razorpay_client.utility.verify_payment_signature(params_dict)

#             # ✅ Update bookings as PAID
#             ServiceBook.objects.filter(comment__icontains=razorpay_order_id).update(
#                 status="complete"
#             )

#             return Response({"status": 200, "message": "Payment verified successfully"})
#         except razorpay.errors.SignatureVerificationError:
#             return Response({"status": 400, "message": "Payment verification failed"}, status=400)