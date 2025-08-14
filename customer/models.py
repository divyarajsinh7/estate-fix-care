from django.db import models
from django.utils import timezone
import random

class CustomerProfile(models.Model):
    ROLE_METHOD_CHOICES = [
        ('user', 'User'),
        ('electrician', 'Electrician'),
        ('admin', 'Admin'),
    ]

    username = models.CharField(max_length=150, unique=True, blank=False, null=False)
    email = models.EmailField(unique=True, blank=False, null=False)
    country_code = models.CharField(max_length=5, blank=False, null=False, default='+91')
    mobile = models.CharField(max_length=12, unique=True, blank=False, null=False)
    role = models.CharField(max_length=20,choices=ROLE_METHOD_CHOICES, blank=False, null=False) # user, electrician,, admin
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    experience_year = models.IntegerField(blank=True, null=True)
    service_skill = models.TextField(blank=True, null=True)
    service_km = models.IntegerField(blank=True, null=True)
    document_type = models.CharField(max_length=20, blank=True, null=True)
    document_file = models.FileField(upload_to='documents/', blank=True, null=True)
    is_gov_verified = models.BooleanField(default=False)
    is_police_verified = models.BooleanField(default=False)
    is_admin_verified = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    wallet_balance = models.FloatField(default=0.0)
    is_blocked = models.BooleanField(default=False)
    blocked_reason = models.TextField(blank=True, null=True)
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField('admin_panel.SubCategory', blank=True, related_name='service_categories')

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return self.username
    
    def create_otp(self):
        self.otp = str(random.randint(100000, 999999))
        self.otp_created_at = timezone.now()
        self.save()
        return self.otp

    def is_otp_valid(self):
        if self.otp_created_at:
            time_difference = timezone.now() - self.otp_created_at
            return time_difference.total_seconds() <= 600  # 10 min
        return False

    def otp_verify(self, post_otp):
        return self.otp == post_otp


class Address(models.Model):
    user = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, blank=False, null=False)  # e.g. Home, Office
    address = models.CharField(max_length=255, blank=False, null=False)
    city = models.CharField(max_length=50, blank=False, null=False)
    state = models.CharField(max_length=50, blank=False, null=False)
    pincode = models.CharField(max_length=10, blank=False, null=False)
    is_default = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_date']

    def __str__(self):
        return f"{self.label} - {self.user.username}"


class SystemLog(models.Model):
    type = models.CharField(max_length=50)  # login, wallet_update, manual_assign, etc.
    performed_by = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL, null=True)
    remark = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type} by {self.performed_by}"