from django.urls import path
from .views import *
from admin_panel.views import *

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('verify-otp/', VerifyOTPAPIView.as_view(), name='verify-otp'),
    path('generate-otp/', GenerateOTPAPIView.as_view(), name='generate-otp'),
    path('login/', LoginSendOTPView.as_view(), name='login-send-otp'),
    path('login/verify-otp/', LoginVerifyOTPView.as_view(), name='login-verify-otp'),
    path("profile/", CustomerProfileView.as_view(), name="customer-profile"),
    path('categories/', CategoryView.as_view()),
    path('categories/<int:category_id>/', CategoryView.as_view()),
    path('subcategories/', SubCategoryView.as_view()),
    path('subcategories/<int:subcategory_id>/', SubCategoryView.as_view()), 
    path("cart/", CartView.as_view()),
    path("cart/<int:item_id>/", CartView.as_view()),
    path('payment/otp/', GeneratePaymentOTPView.as_view(), name='payment-generate-otp'),
    path('payment/checkout/', RazorpayCheckoutView.as_view(), name='razorpay-checkout'),
]