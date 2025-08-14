from django.urls import path
from .views import *

urlpatterns = [
    path('categories/', CategoryView.as_view()),
    path('categories/<int:category_id>/', CategoryView.as_view()),
    path('subcategories/', SubCategoryView.as_view()),
    path('subcategories/<int:subcategory_id>/', SubCategoryView.as_view()), 
]