from django.db import models
from django.conf import settings
from wallets.models import Wallet
import random

class Withdrawal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='withdrawals')
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10)
    address = models.CharField(max_length=255)           # destination address or description
    transaction_code = models.CharField(max_length=30, unique=True, blank=True)
    method = models.CharField(
        max_length=20,
        choices=[
            ('BANK', 'Bank Transfer'),
            ('CRYPTO', 'Cryptocurrency'),
            ('PAYPAL', 'PayPal')
        ],
        default='CRYPTO'
    )
    details = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('CONFIRMED', 'Confirmed'),
            ('PROCESSING', 'Processing'),
            ('COMPLETED', 'Completed'),
            ('REJECTED', 'Rejected')
        ],
        default='PENDING'
    )
    confirmation_code = models.CharField(max_length=6, blank=True)
    approved_by = models.ForeignKey('admin_panel.Admin', on_delete=models.SET_NULL, null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Withdrawal [{self.transaction_code or self.id}] of {self.amount} {self.currency} by {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.confirmation_code:
            self.confirmation_code = f"{random.randint(100000, 999999)}"
        if not self.transaction_code:
            code = f"PV-WD-{random.randint(100000, 999999)}"
            while Withdrawal.objects.filter(transaction_code=code).exists():
                code = f"PV-WD-{random.randint(100000, 999999)}"
            self.transaction_code = code
        super().save(*args, **kwargs)
