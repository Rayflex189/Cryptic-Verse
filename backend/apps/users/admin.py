from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.shortcuts import redirect, get_object_or_404
from django.urls import path

User = get_user_model()

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'full_name', 'verification_status',
        'is_email_verified', 'verify_account_action', 'date_joined', 'is_active'
    )
    list_filter = ('verification_status', 'is_email_verified', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('username', 'email', 'full_name', 'phone')
    ordering = ('-date_joined',)
    actions = ['verify_selected_accounts', 'mark_selected_accounts_pending']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Account Verification System', {
            'fields': ('verification_status', 'is_email_verified', 'is_phone_verified', 'is_frozen')
        }),
        ('Financial Balances', {
            'fields': ('balance', 'profit_balance', 'kyc_status', 'kyc_level', 'vip_level')
        }),
    )

    def verify_account_action(self, obj):
        if obj.verification_status == 'VERIFIED' or obj.is_email_verified:
            return format_html(
                '<a class="button" style="background-color: #eab308; color: #000; font-weight: bold; padding: 3px 8px; border-radius: 4px;" href="{}">Set Pending</a>',
                f"/django-admin/users/user/{obj.id}/toggle-verification/"
            )
        else:
            return format_html(
                '<a class="button" style="background-color: #10b981; color: #000; font-weight: bold; padding: 3px 8px; border-radius: 4px;" href="{}">Verify Account</a>',
                f"/django-admin/users/user/{obj.id}/toggle-verification/"
            )
    verify_account_action.short_description = "Quick Verification Action"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/toggle-verification/', self.admin_site.admin_view(self.toggle_verification_view), name='user_toggle_verification'),
        ]
        return custom_urls + urls

    def toggle_verification_view(self, request, object_id):
        user = get_object_or_404(User, pk=object_id)
        if user.verification_status == 'VERIFIED' or user.is_email_verified:
            user.verification_status = 'PENDING'
            user.is_email_verified = False
            user.save(update_fields=['verification_status', 'is_email_verified'])
            messages.warning(request, f"Account @{user.username} verification status changed to PENDING.")
        else:
            user.verification_status = 'VERIFIED'
            user.is_email_verified = True
            user.save(update_fields=['verification_status', 'is_email_verified'])
            messages.success(request, f"Account @{user.username} successfully VERIFIED.")
        return redirect('/django-admin/users/user/')

    @admin.action(description="Verify selected user accounts")
    def verify_selected_accounts(self, request, queryset):
        count = 0
        for user in queryset:
            user.verification_status = 'VERIFIED'
            user.is_email_verified = True
            user.save(update_fields=['verification_status', 'is_email_verified'])
            count += 1
        messages.success(request, f"Successfully verified {count} user account(s).")

    @admin.action(description="Mark selected user accounts as Pending Verification")
    def mark_selected_accounts_pending(self, request, queryset):
        count = 0
        for user in queryset:
            user.verification_status = 'PENDING'
            user.is_email_verified = False
            user.save(update_fields=['verification_status', 'is_email_verified'])
            count += 1
        messages.warning(request, f"Set {count} user account(s) to PENDING verification.")
