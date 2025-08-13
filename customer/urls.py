from django.urls import path
from .views import *

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPAPIView.as_view(), name='verify-otp'),
    path('generate-otp/', GenerateOTPAPIView.as_view(), name='generate-otp'),
    path('login/', LoginSendOTPView.as_view(), name='login-send-otp'),
    path('login/verify-otp/', LoginVerifyOTPView.as_view(), name='login-verify-otp'),
]