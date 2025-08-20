from django.contrib import admin
from .models import CustomerProfile, Address
from django.utils.html import format_html


class AddressInline(admin.TabularInline):  
    model = Address
    extra = 1


@admin.register(CustomerProfile)
class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'username', 'email', 'mobile', 'role',
        'is_verified', 'is_admin_verified', 'wallet_balance', 'is_blocked', 'approval_status'
    )
    search_fields = ('username', 'email', 'mobile')
    list_filter = ('role', 'is_verified', 'is_blocked', 'is_admin_verified')
    inlines = [AddressInline]
    readonly_fields = ('otp', 'otp_created_at', 'created_date', 'updated_date')
    list_display_links = (
        'id', 'username', 'email', 'mobile', 'role',
        'is_verified', 'is_admin_verified', 'wallet_balance', 'is_blocked', 'approval_status'
    )

    # Add custom actions
    actions = ['approve_electrician', 'reject_electrician']

    def approval_status(self, obj):
        """Show colored status in list view"""
        if obj.role == "electrician":
            if obj.is_admin_verified:
                return format_html('<span style="color: green;">Approved</span>')
            elif obj.is_blocked:
                return format_html('<span style="color: red;">Rejected</span>')
            return format_html('<span style="color: orange;">Pending</span>')
        return "-"
    approval_status.short_description = "Approval Status"

    def approve_electrician(self, request, queryset):
        updated = queryset.filter(role="electrician").update(is_admin_verified=True, is_verified=True, is_blocked=False)
        self.message_user(request, f"{updated} electrician(s) approved.")
    approve_electrician.short_description = "Approve selected electricians"

    def reject_electrician(self, request, queryset):
        updated = queryset.filter(role="electrician").update(is_admin_verified=False, is_verified=False, is_blocked=True)
        self.message_user(request, f"{updated} electrician(s) rejected.")
    reject_electrician.short_description = "Reject selected electricians"


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'label', 'address', 'city',
        'state', 'pincode', 'is_default'
    )
    search_fields = ('user__username', 'city', 'state', 'pincode')
    list_filter = ('city', 'state', 'is_default')
    list_display_links = (
        'id', 'user', 'label', 'address', 'city',
        'state', 'pincode', 'is_default'
    )

    fields = (
        'user', 'label', 'address', 'city', 'state',
        'pincode', 'is_default'
    )

    readonly_fields = ('id',)