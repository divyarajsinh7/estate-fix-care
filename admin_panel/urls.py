from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('categories/', CategoryView.as_view()),
    path('categories/<int:category_id>/', CategoryView.as_view()),
    path('subcategories/', SubCategoryView.as_view()),
    path('categories/<int:category_id>/subcategories/', SubCategoryView.as_view()),
    path('subcategories/<int:subcategory_id>/items/', SubCategoryItemView.as_view()),
    path('items/<int:item_id>/', SubCategoryItemView.as_view()),  
    path("pending-profiles/", PendingProfileApprovalView.as_view(), name="pending-profiles-list"),
    path("pending-profiles/<int:pk>/", PendingProfileApprovalView.as_view(), name="pending-profile-approve"),
    path("pending-bank-details/", PendingBankDetailApprovalView.as_view()),
    path("pending-bank-details/<int:pk>/", PendingBankDetailApprovalView.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)