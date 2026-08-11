from django.contrib import admin
from .models import CompanyWallet, PlatformSetting

@admin.register(CompanyWallet)
class CompanyWalletAdmin(admin.ModelAdmin):
    list_display = ('wallet_name', 'wallet_address', 'network', 'is_active', 'updated_at')
    list_filter = ('is_active', 'network')
    search_fields = ('wallet_name', 'wallet_address', 'network')
    list_editable = ('is_active',)

@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    list_display = (
        '__str__', 'vip_upgrade_fee', 'company_wallet_address', 'wallet_network',
        'conversion_fee_pct', 'enable_currency_converter', 'enable_vip_upgrade', 'enable_withdrawals'
    )
    fieldsets = (
        ('VIP Upgrade Settings', {
            'fields': ('vip_upgrade_fee', 'company_wallet_address', 'wallet_network', 'enable_vip_upgrade')
        }),
        ('Currency Converter Settings', {
            'fields': ('conversion_fee_pct', 'enable_currency_converter')
        }),
        ('Withdrawals Settings', {
            'fields': ('enable_withdrawals',)
        }),
    )

    def has_add_permission(self, request):
        # Prevent creating multiple platform settings rows
        if PlatformSetting.objects.exists():
            return False
        return super().has_add_permission(request)
