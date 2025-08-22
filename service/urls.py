from django.urls import path
from .views import *
from customer.views import LoginSendOTPView

urlpatterns = [
    path('register/', ServiceProviderRegisterAPIView.as_view(), name='register'),
    path('register/verfy-otp/', VerifyRegisterOTPAPIView.as_view(), name='register'),
    path('login/', LoginSendOTPView.as_view(), name='login-send-otp'),
    path('login/verify-otp/', LoginVerifyServiceOTPView.as_view(), name='login-verify-otp'),
    path('profile/', SerivceProviderProfileView.as_view(), name='profile'),
    path("bank-details/", BankDetailView.as_view(), name="bank-detail-list-create"),
    path("bank-details/<int:pk>/", BankDetailView.as_view(), name="bank-detail-update-delete"),
]