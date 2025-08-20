from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .serializers import ServiceRegisterSerializer, ServiceProfileSerializer
from customer.models import CustomerProfile, SystemLog
from rest_framework_simplejwt.tokens import RefreshToken
from user_agents import parse

class ElectricianRegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ServiceRegisterSerializer(data=request.data)
        if serializer.is_valid():
            mobile = serializer.validated_data['mobile']

            if CustomerProfile.objects.filter(mobile=mobile).exists():
                return Response({
                    "status": 400,
                    "message": "User with this mobile already exists."
                }, status=400)

            electrician = serializer.save(
                is_admin_verified=False
            )

            otp = electrician.create_otp()
            
            return Response({
                "status": 200,
                "message": "OTP sent successfully. Please verify to complete registration.",
                "otp" : otp,  # Assuming otp is generated and saved in the model
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