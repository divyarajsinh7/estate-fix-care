from django.db import models
from customer.models import CustomerProfile
from django.core.validators import MinValueValidator, MaxValueValidator


class Category(models.Model):
    category_name = models.CharField(max_length=100,blank=False, null=False, unique=True)
    image = models.FileField(upload_to='category_images/', blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.category_name


class SubCategory(models.Model):  # This is your "Service or sub_category"
    name = models.CharField(max_length=100,blank=False, null=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='subcategories')
    description = models.TextField(blank=False, null=False)
    cover_image = models.FileField(upload_to='service_covers/', blank=True, null=True)
    image = models.FileField(upload_to='subcategory_image/', blank=True, null=True)
    section = models.CharField(max_length=50,blank=False, null=False)  # most, premium, new, nearby
    steps = models.TextField(blank=False, null=False)
    faqs = models.TextField(blank=False, null=False)
    price = models.CharField(max_length=50,blank=False, null=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SubCategoryItem(models.Model):
    subcategory = models.ForeignKey(SubCategory, on_delete=models.CASCADE, related_name="items")
    step_no = models.PositiveIntegerField()
    title = models.CharField(max_length=100)
    description = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subcategory.name} - Step {self.step_no}: {self.title}"