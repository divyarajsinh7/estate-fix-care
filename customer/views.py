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




class RegisterAPIView(APIView):
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
    """Step 1: Send OTP to user."""
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
    """Step 2: Verify OTP and login."""
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