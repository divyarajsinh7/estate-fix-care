from django.contrib import admin
from .models import *


class SubCategoryInline(admin.TabularInline):  
    model = SubCategory
    extra = 1  # how many empty forms you want to show


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'category_name', 'created_date', 'updated_date')
    list_display_links = ('id', 'category_name', 'created_date', 'updated_date') 
    search_fields = ('category_name',)
    readonly_fields = ('created_date', 'updated_date')
    ordering = ('-created_date',)


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'category', 'section', 'price', 'created_date', 'updated_date')
    list_display_links = ('id', 'name', 'category', 'section', 'price', 'created_date', 'updated_date')
    list_filter = ('category', 'section')
    search_fields = ('name', 'description', 'faqs')
    ordering = ('-created_date',)
    readonly_fields = ('created_date', 'updated_date')


@admin.register(SubCategoryItem)
class SubCategoryItemAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "subcategory", "created_date", "updated_date")
    list_filter = ("subcategory",)
    search_fields = ("title", "subcategory__name")
    ordering = ("-created_date",)
