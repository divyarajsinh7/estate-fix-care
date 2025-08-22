from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import *
from customer.models import CustomerProfile, SystemLog, PendingProfileUpdate, BankDetail, PendingBankDetailUpdate
from rest_framework_simplejwt.tokens import RefreshToken
from user_agents import parse
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied
from rest_framework import status


class ServiceProviderRegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ServiceRegisterSerializer(data=request.data)
        if serializer.is_valid():
            mobile = serializer.validated_data['mobile']

            # Check if mobile already exists
            if CustomerProfile.objects.filter(mobile=mobile).exists():
                return Response({
                    "status": 400,
                    "message": "User with this mobile already exists."
                }, status=400)

            # Save service provider with default flags
            service_provider = serializer.save(
                is_admin_verified=False
            )

            # Generate OTP
            otp = service_provider.create_otp()

            return Response({
                "status": 200,
                "message": "OTP sent successfully. Please verify to complete registration.",
                "otp": otp,  # just for debugging, remove in production
                "role": service_provider.role
            })

        return Response({
            "status": 400,
            "message": "Invalid data",
            "errors": serializer.errors
        }, status=400)
    

class VerifyRegisterOTPAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        country_code = request.data.get("country_code")
        mobile = request.data.get("mobile")
        otp_entered = request.data.get("otp")

        if not country_code or not mobile or not otp_entered:
            return Response(
                {"status": 400, "message": "country_code, mobile, and otp are required"},
                status=400
            )

        try:
            customer = CustomerProfile.objects.get(country_code=country_code, mobile=mobile)
        except CustomerProfile.DoesNotExist:
            return Response({"status": 404, "message": "User not found"}, status=404)

        # Check OTP expiry
        if not customer.is_otp_valid():
            return Response({"status": 400, "message": "OTP expired"}, status=400)

        # Match OTP
        if customer.otp == otp_entered:
            # Clear OTP after successful verification
            customer.otp = None
            customer.otp_created_at = None
            customer.save()

            return Response({
                "status": 200,
                "message": "Registration successful. Your request is under review by the admin."
            })
        else:
            return Response({"status": 400, "message": "Invalid OTP"}, status=400)
    

class LoginVerifyServiceOTPView(APIView):
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

        # Check if OTP is valid
        if not user.is_otp_valid():
            return Response({"status": 400, "message": "OTP expired"}, status=400)

        # Verify OTP match
        if not user.otp_verify(otp_entered):
            return Response({"status": 400, "message": "Invalid OTP"}, status=400)

        # OTP verified → clear OTP fields
        user.otp = None
        user.otp_created_at = None
        user.save()

        if not user.is_admin_verified:
            return Response({
                "status": 403,
                "message": "Your profile is under review by the admin. Please be patient."
            }, status=403)
        
        if user.is_blocked:
            return Response({
                "status": 403,
                "message": f"Your profile is blocked: {user.blocked_reason}. Please contact admin to approve your profile."
            }, status=403)

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

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        # ✅ Serialize full user data
        user_data = ServiceProfileSerializer(user).data

        return Response({
            "status": 200,
            "message": "Login success",
            "data": {
                "user": user_data,
                "access_token": str(access),
                "refresh_token": str(refresh),
                "device_type": device_type,
                "os": os_name,
                "browser": browser
            }
        }, status=200)
    

class SerivceProviderProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request):
        profile = get_object_or_404(CustomerProfile, email=request.user.email)
        if profile.role != "service_provider":
            raise PermissionDenied("Only service providers can access this endpoint.")
        return profile

    def get(self, request):
        profile = self.get_object(request)
        serializer = ServiceProviderProfileSerializer(profile, context={'request': request})
        return Response({
            "status": 200,
            "message": "Profile retrieved",
            "data": serializer.data
        })

    def patch(self, request):
        profile = self.get_object(request)

        # Instead of saving directly → store request as pending update
        pending_update = PendingProfileUpdate.objects.create(
            profile=profile,
            data=request.data
        )

        return Response({
            "status": 202,
            "message": "Update request submitted for admin approval",
            "pending_id": pending_update.id
        })

    def delete(self, request):
        profile = self.get_object(request)
        profile.delete()
        return Response({"status": 200, "message": "Profile deleted", "data": {}})


class BankDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_profile(self, request):
        """Fetch logged-in user's service_provider profile"""
        return get_object_or_404(
            CustomerProfile, email=request.user.email, role="service_provider"
        )

    def get(self, request):
        profile = self.get_profile(request)
        bank_details = profile.bank_details.all()
        serializer = BankDetailSerializer(bank_details, many=True)
        return Response(
            {"status": 200, "message": "Bank details retrieved", "data": serializer.data}
        )

    def post(self, request):
        profile = self.get_profile(request)
        serializer = BankDetailSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(customer=profile)
            return Response(
                {"status": 201, "message": "Bank detail added", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response({"status": 400, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """Instead of updating directly, create a pending update request"""
        profile = self.get_profile(request)
        bank_detail = get_object_or_404(BankDetail, id=pk, customer=profile)

        # Save the update request into PendingBankDetailUpdate
        pending_update = PendingBankDetailUpdate.objects.create(
            bank_detail=bank_detail,
            data=request.data
        )

        return Response(
            {
                "status": 202,
                "message": "Bank detail update submitted for admin approval",
                "pending_update_id": pending_update.id,
            },
            status=status.HTTP_202_ACCEPTED,
        )

    def delete(self, request, pk):
        profile = self.get_profile(request)
        bank_detail = get_object_or_404(BankDetail, id=pk, customer=profile)
        bank_detail.delete()
        return Response({"status": 200, "message": "Bank detail deleted"})