from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone

class InvestmentPlan(models.Model):
    name = models.CharField(max_length=100, unique=True)
    min_deposit = models.DecimalField(max_digits=20, decimal_places=8)
    max_deposit = models.DecimalField(max_digits=20, decimal_places=8)
    daily_profit_percent = models.DecimalField(max_digits=5, decimal_places=2)  # e.g., 0.5
    duration_days = models.PositiveIntegerField()      # number of days
    compounding = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Investment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='investments')
    plan = models.ForeignKey(InvestmentPlan, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=20, decimal_places=8)
    currency = models.CharField(max_length=10)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('ACTIVE', 'Active'), ('COMPLETED', 'Completed'), ('CANCELLED', 'Cancelled')],
        default='ACTIVE'
    )
    profit_accrued = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    auto_reinvest = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s investment in {self.plan.name}"

    def save(self, *args, **kwargs):
        if not self.end_date:
            base_date = self.start_date if self.start_date else timezone.now()
            self.end_date = base_date + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)
