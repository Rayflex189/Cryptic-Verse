from django.db import models
from django.conf import settings
from wallets.models import Wallet

class Deposit(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deposits')
    wallet = models.ForeignKey(Wallet, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10)
    transaction_hash = models.CharField(max_length=255, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('CONFIRMED', 'Confirmed'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )
    proof_image = models.ImageField(upload_to='deposits/', null=True, blank=True)
    admin_notes = models.TextField(blank=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Deposit of {self.amount} {self.currency} by {self.user.username}"
