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
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('ACTIVE', 'Active'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled'),
            ('PAUSED', 'Paused')
        ],
        default='ACTIVE'
    )
    expected_profit = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    expected_profit_type = models.CharField(
        max_length=20,
        choices=[('PERCENT', 'Percentage'), ('ABSOLUTE', 'Absolute Amount')],
        default='PERCENT'
    )
    distribution_frequency = models.CharField(
        max_length=20,
        choices=[
            ('HOURLY', 'Hourly'),
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('MATURITY', 'At Maturity'),
            ('CUSTOM_6H', 'Every 6 Hours'),
            ('CUSTOM_12H', 'Every 12 Hours'),
        ],
        default='DAILY'
    )
    is_automated = models.BooleanField(default=True)
    is_paused = models.BooleanField(default=False)
    last_payout_at = models.DateTimeField(null=True, blank=True)
    next_payout_at = models.DateTimeField(null=True, blank=True)
    payouts_made = models.PositiveIntegerField(default=0)
    total_payouts_expected = models.PositiveIntegerField(default=1)
    amount_per_payout = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    
    profit_accrued = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    auto_reinvest = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s investment in {self.plan.name}"

    def save(self, *args, **kwargs):
        # 1. Start date check
        if not self.start_date:
            self.start_date = timezone.now()

        # 2. Get duration from plan if end_date is not set
        duration_days = self.plan.duration_days
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=duration_days)

        # 3. Handle default expected_profit from plan's daily_profit_percent if expected_profit is 0
        if self.expected_profit == 0 and self.expected_profit_type == 'PERCENT':
            self.expected_profit = self.plan.daily_profit_percent * duration_days

        # 4. Calculate total expected profit
        if self.expected_profit_type == 'PERCENT':
            total_profit = self.amount * (self.expected_profit / 100)
        else:
            total_profit = self.expected_profit

        # 5. Set interval hours and total payouts count
        if self.distribution_frequency == 'HOURLY':
            hours = 1
        elif self.distribution_frequency == 'CUSTOM_6H':
            hours = 6
        elif self.distribution_frequency == 'CUSTOM_12H':
            hours = 12
        elif self.distribution_frequency == 'DAILY':
            hours = 24
        elif self.distribution_frequency == 'WEEKLY':
            hours = 168
        else: # At maturity
            hours = duration_days * 24

        total_hours = max(24, duration_days * 24)
        expected_intervals = max(1, total_hours // hours)

        self.total_payouts_expected = expected_intervals
        self.amount_per_payout = total_profit / expected_intervals

        # 6. Set initial next_payout_at
        if not self.next_payout_at and self.status in ['PENDING', 'ACTIVE']:
            self.next_payout_at = self.start_date + timedelta(hours=hours)

        # 7. Status transition logic
        now = timezone.now()
        if self.status == 'PENDING' and self.start_date <= now:
            self.status = 'ACTIVE'
            
        super().save(*args, **kwargs)
