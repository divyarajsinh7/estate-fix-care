from django.contrib import admin
from .models import CustomerProfile, Address, BankDetail, PendingProfileUpdate, PendingBankDetailUpdate
from django.utils.html import format_html
from .serializers import CustomerProfileSerializer


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
    actions = ['approve_service_provider', 'reject_service_provider']

    def approval_status(self, obj):
        """Show colored status in list view"""
        if obj.role == "service_provider":
            if obj.is_admin_verified:
                return format_html('<span style="color: green;">Approved</span>')
            elif obj.is_blocked:
                return format_html('<span style="color: red;">Rejected</span>')
            return format_html('<span style="color: orange;">Pending</span>')
        return "-"
    approval_status.short_description = "Approval Status"

    def approve_service_provider(self, request, queryset):
        updated = queryset.filter(role="service_provider").update(
            is_admin_verified=True, is_verified=True, is_blocked=False
        )
        self.message_user(request, f"{updated} service provider(s) approved.")
    approve_service_provider.short_description = "Approve selected service providers"

    def reject_service_provider(self, request, queryset):
        updated = queryset.filter(role="service_provider").update(
            is_admin_verified=False, is_verified=False, is_blocked=True
        )
        self.message_user(request, f"{updated} service provider(s) rejected.")
    reject_service_provider.short_description = "Reject selected service providers"


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





@admin.register(PendingProfileUpdate)
class PendingProfileUpdateAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "created_at", "approved", "reviewed")
    list_filter = ("approved", "reviewed", "created_at")
    search_fields = ("profile__username", "profile__email")

    actions = ["approve_updates", "reject_updates"]

    def approve_updates(self, request, queryset):
        for pending in queryset.filter(reviewed=False):
            data = pending.data
            profile = pending.profile

            # Apply profile changes
            serializer = CustomerProfileSerializer(profile, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()

            # Apply address changes if present
            addresses_data = data.get("addresses", [])
            for addr in addresses_data:
                addr_id = addr.get("id")

                # 🔑 Map external keys to actual model fields
                addr["address"] = addr.pop("street", addr.get("address", None))
                addr["pincode"] = addr.pop("zip_code", addr.get("pincode", None))

                if addr_id:
                    Address.objects.filter(id=addr_id, user=profile).update(**addr)
                else:
                    Address.objects.create(user=profile, **addr)

            pending.approved = True
            pending.reviewed = True
            pending.save()

        self.message_user(request, "Selected profile updates approved and applied.")

    approve_updates.short_description = "Approve and apply selected profile updates"

    def reject_updates(self, request, queryset):
        queryset.update(approved=False, reviewed=True)
        self.message_user(request, "Selected profile updates rejected.")

    reject_updates.short_description = "Reject selected profile updates"


@admin.register(BankDetail)
class BankDetailAdmin(admin.ModelAdmin):
    list_display = ["customer", "bank_name", "account_number", "is_approved"]


@admin.register(PendingBankDetailUpdate)
class PendingBankDetailUpdateAdmin(admin.ModelAdmin):
    list_display = ("bank_detail", "customer_name", "created_at", "approved", "reviewed")
    actions = ["approve_updates", "reject_updates"]

    def customer_name(self, obj):
        return obj.bank_detail.customer  # shows linked customer
    customer_name.short_description = "Customer"

    def approve_updates(self, request, queryset):
        for pending in queryset:
            bank = pending.bank_detail
            # apply only changed fields from JSON
            for field, value in pending.data.items():
                setattr(bank, field, value)

            bank.is_approved = True
            bank.save()
            pending.delete()

        self.message_user(request, "✅ Selected pending updates approved.")

    def reject_updates(self, request, queryset):
        queryset.delete()
        self.message_user(request, "❌ Selected pending updates rejected.")
