from django.db import models
from django.utils import timezone
import random

class CustomerProfile(models.Model):
    ROLE_METHOD_CHOICES = [
        ('user', 'User'),
        ('service_provider', 'Service Provider'),
        ('admin', 'Admin'),
    ]

    username = models.CharField(max_length=150, blank=False, null=False)
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
    date_of_birth = models.DateField(blank=True, null=True)
    degree = models.CharField(max_length=100, blank=True, null=True)
    company_policy = models.TextField(blank=True, null=True)

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
    

class BankDetail(models.Model):
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name="bank_details")
    account_holder_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=30)
    ifsc_code = models.CharField(max_length=20)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    branch_name = models.CharField(max_length=100, blank=True, null=True)
    upi_id = models.CharField(max_length=100, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.account_holder_name} - {self.bank_name} ({self.account_number[-4:]})"


class SystemLog(models.Model):
    type = models.CharField(max_length=50)  # login, wallet_update, manual_assign, etc.
    performed_by = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL, null=True)
    remark = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type} by {self.performed_by}"
    

class Cart(models.Model):
    user = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='cart')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"


class ServiceCart(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed')

    ]
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='services')
    service = models.ForeignKey("admin_panel.SubCategory", on_delete=models.CASCADE)
    num_of_tech = models.IntegerField(default=1)
    qty = models.IntegerField(default=1)
    price = models.FloatField(default=0.0)
    total_price = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES ,default='pending')
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f"{self.service.name} x {self.qty}"


class ServiceBook(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assign', 'Assigned'),
        ('arriving', 'Arriving'),
        ('complete', 'Complete'),
        ('cancel', 'Cancel')

    ]
    ACTION_CHOICE = [
        ('approve', 'Approve'),
        ('reject', 'Reject')
    ]
    user = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='bookings')
    service = models.ForeignKey("admin_panel.SubCategory", on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES , default='assign')
    technician_required = models.IntegerField(default=1)
    assigned_technician = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs')
    is_agency_booking = models.BooleanField(default=False)
    assigned_agency = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='agency_bookings')
    is_manual_assignment = models.BooleanField(default=False)
    assigned_by_admin = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='admin_assigned_jobs')
    manual_assignment_reason = models.TextField(blank=True, null=True)
    manual_assignment_date = models.DateTimeField(blank=True, null=True)

    is_scheduled = models.BooleanField(default=False)
    scheduled_date_time = models.DateTimeField(blank=True, null=True)

    accept_at = models.DateTimeField(blank=True, null=True)
    arrived_at = models.DateTimeField(blank=True, null=True)

    quatation_amt = models.FloatField(default=0.0)
    otp_required = models.BooleanField(default=True)
    service_start_otp = models.CharField(max_length=6, blank=True, null=True)
    otp_generated_at = models.DateTimeField(blank=True, null=True)
    otp_verified_at = models.DateTimeField(blank=True, null=True)
    otp_verified_by = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='otp_verified_jobs')

    action = models.CharField(max_length=20, choices=ACTION_CHOICE, default='Approve')  # start, reject
    job_started_at = models.DateTimeField(blank=True, null=True)
    photo = models.ImageField(upload_to='job_photos/', blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    is_bill_generated = models.BooleanField(default=False)
    pdf_url = models.CharField(max_length=255, blank=True, null=True)
    is_repeated = models.BooleanField(default=False)
    triggered = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking #{self.id} by {self.user.username}"


class Notification(models.Model):
    RECIPIENT_TYPE_CHOICES = [
    ('admin', 'Admin'),
    ('user', 'User'),
    ('service_provider', 'Service Provider'),
    ]
    NOTIFICATION_CHANNEL_CHOICES = [
    ('app', 'App'),
    ('email', 'Email'),
    ('sms', 'SMS'),
    ]
    NOTIFICATION_TYPE_CHOICES = [
    ('booking', 'Booking'),
    ('payment', 'Payment'),
    ('profile', 'Profile'),
    ('wallet', 'Wallet'),
    ('complaint', 'Complaint'),
    ('arrival', 'Arrival'),
    ]

    user = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    service_provider  = models.ForeignKey(CustomerProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='service_notifications')
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_TYPE_CHOICES,blank=False, null=False, default='user')  # admin, user, electrician
    title = models.CharField(max_length=100, blank=False, null=False)
    message = models.TextField(blank=False, null=False)
    type = models.CharField(max_length=50,choices=NOTIFICATION_TYPE_CHOICES ,blank=False, null=False)# booking, payment, profile, wallet, complaint, arrival, etc.
    channel = models.CharField(max_length=20, blank=False, choices=NOTIFICATION_CHANNEL_CHOICES,null=False, default='app')  # app, email, sms
    is_sent = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"To {self.recipient_type} - {self.title}"