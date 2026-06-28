from django.db import models
from django.conf import settings

class AdminWalletAddress(models.Model):
    currency = models.CharField(max_length=10, unique=True)   # BTC, ETH, USDT, BNB, SOL
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.currency}: {self.address}"

class Wallet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallets')
    currency = models.CharField(max_length=10)   # BTC, ETH, USDT, BNB, SOL
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    locked_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'currency')

    def __str__(self):
        return f"{self.user.username}'s {self.currency} Wallet"

    @property
    def address(self):
        try:
            return AdminWalletAddress.objects.get(currency=self.currency).address
        except AdminWalletAddress.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.currency == 'USDT':
            user = self.user
            if user.balance != self.balance:
                user.balance = self.balance
                user.save(update_fields=['balance'])
