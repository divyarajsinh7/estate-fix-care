from django.contrib import admin
from .models import CustomerProfile, Address


class AddressInline(admin.TabularInline):  
    model = Address
    extra = 1


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'mobile', 'role', 'is_verified', 'wallet_balance', 'is_blocked')
    search_fields = ('username', 'email', 'mobile')
    list_filter = ('role', 'is_verified', 'is_blocked', 'is_admin_verified')
    inlines = [AddressInline]


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'label', 'address', 'city', 'state', 'pincode', 'is_default')
    search_fields = ('user__username', 'city', 'state', 'pincode')
    list_filter = ('city', 'state', 'is_default')