from django.db import models

class CompanyWallet(models.Model):
    wallet_name = models.CharField(max_length=100)
    wallet_address = models.CharField(max_length=255)
    network = models.CharField(max_length=50, help_text="e.g. ERC20, TRC20, BEP20")
    is_active = models.BooleanField(default=False, help_text="Only one wallet can be active at a time.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            CompanyWallet.objects.exclude(pk=self.pk).update(is_active=False)

    def __str__(self):
        return f"{self.wallet_name} ({self.network}) - {'ACTIVE' if self.is_active else 'Inactive'}"


class PlatformSetting(models.Model):
    vip_upgrade_fee = models.DecimalField(max_digits=20, decimal_places=2, default=200.00)
    company_wallet_address = models.CharField(max_length=255, default='0x71C7656EC7ab88b098defB751B7401B5f6d8976F')
    wallet_network = models.CharField(max_length=50, default='ERC20')
    conversion_fee_pct = models.DecimalField(max_digits=5, decimal_places=2, default=1.00, help_text="Default 1.00 for 1%")
    enable_currency_converter = models.BooleanField(default=True)
    enable_vip_upgrade = models.BooleanField(default=True)
    enable_withdrawals = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Platform Setting"
        verbose_name_plural = "Platform Settings"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Ensure single row configuration
        PlatformSetting.objects.exclude(pk=self.pk).delete()

    @classmethod
    def get_settings(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return "Global Platform Settings Configuration"
