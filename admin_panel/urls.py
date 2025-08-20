from django.urls import path
from .views import *
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('categories/', CategoryView.as_view()),
    path('categories/<int:category_id>/', CategoryView.as_view()),
    path('subcategories/', SubCategoryView.as_view()),
    path('subcategories/<int:subcategory_id>/', SubCategoryView.as_view()), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)