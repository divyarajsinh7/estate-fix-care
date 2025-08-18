from django.contrib import admin
from .models import Category, SubCategory


class SubCategoryInline(admin.TabularInline):  
    model = SubCategory
    extra = 1  # how many empty forms you want to show


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name', 'created_date', 'updated_date')
    search_fields = ('category_name',)
    inlines = [SubCategoryInline]


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'section', 'price', 'created_date', 'updated_date')
    list_filter = ('category', 'section')
    search_fields = ('name', 'description', 'faqs')