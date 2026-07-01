from django.db import models
from django.contrib.auth.models import AbstractUser
from core.encryption import encrypt_value, decrypt_value
import uuid

class VIPLevel(models.Model):
    level = models.PositiveSmallIntegerField(unique=True)  # 1,2,3
    name = models.CharField(max_length=50)                 # "VIP 1", etc.
    min_balance = models.DecimalField(max_digits=20, decimal_places=8)
    benefits = models.JSONField(default=list)              # list of strings

    def __str__(self):
        return self.name

class User(AbstractUser):
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    
    ssn_encrypted = models.CharField(max_length=255, blank=True, db_column='ssn')
    
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    kyc_status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('VERIFIED', 'Verified'),
            ('REJECTED', 'Rejected'),
            ('LEVEL_1', 'Level 1'),
            ('LEVEL_2', 'Level 2'),
            ('LEVEL_3', 'Level 3 VIP')
        ],
        default='PENDING'
    )
    kyc_level = models.PositiveSmallIntegerField(default=1)  # 1,2,3
    vip_level = models.ForeignKey(VIPLevel, on_delete=models.SET_NULL, null=True, blank=True)
    referral_code = models.CharField(max_length=20, unique=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    profit_balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    active_investment_override = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    profit_accrued_override = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    referral_bonus_override = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    last_profit_accrual = models.DateTimeField(null=True, blank=True)
    is_frozen = models.BooleanField(default=False)
    is_automation_enabled = models.BooleanField(default=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)
    profile_picture = models.URLField(max_length=500, blank=True, null=True)
    password_reset_otp = models.CharField(max_length=6, blank=True, null=True)
    password_reset_otp_created_at = models.DateTimeField(blank=True, null=True)
    
    otp_secret = models.CharField(max_length=32, blank=True)
    is_2fa_enabled = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    email = models.EmailField(unique=True)

    @property
    def ssn(self):
        return decrypt_value(self.ssn_encrypted)

    @ssn.setter
    def ssn(self, value):
        self.ssn_encrypted = encrypt_value(value)

    @property
    def active_investment(self):
        if self.active_investment_override is not None:
            return self.active_investment_override
        return self.investments.filter(status='ACTIVE').aggregate(models.Sum('amount'))['amount__sum'] or 0

    @property
    def profit_accrued(self):
        if self.profit_accrued_override is not None:
            return self.profit_accrued_override
        return self.investments.filter(status='ACTIVE').aggregate(models.Sum('profit_accrued'))['profit_accrued__sum'] or 0

    @property
    def referral_bonus(self):
        if self.referral_bonus_override is not None:
            return self.referral_bonus_override
        return self.transactions.filter(type='REFERRAL_BONUS').aggregate(models.Sum('amount'))['amount__sum'] or 0

    def save(self, *args, **kwargs):
        if not self.referral_code:
            self.referral_code = str(uuid.uuid4())[:8].upper()
            
        is_new = self.pk is None
        old_balance = None
        if not is_new:
            try:
                old_balance = User.objects.get(pk=self.pk).balance
            except User.DoesNotExist:
                pass
                
        # Only sync balance if it's explicitly being saved or if update_fields is not specified
        update_fields = kwargs.get('update_fields')
        is_balance_saved = False
        if is_new:
            is_balance_saved = True
        elif update_fields is None:
            is_balance_saved = True
        elif 'balance' in update_fields:
            is_balance_saved = True

        super().save(*args, **kwargs)
        
        if is_balance_saved:
            from wallets.models import Wallet
            wallet, created = Wallet.objects.get_or_create(user=self, currency='USDT')
            if created or (old_balance is not None and old_balance != self.balance):
                if wallet.balance != self.balance:
                    wallet.balance = self.balance
                    wallet.save(update_fields=['balance'])



class VIPUpgradeRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vip_upgrades')
    screenshot = models.FileField(upload_to='vip_upgrades/', null=True, blank=True)
    amount = models.DecimalField(max_digits=20, decimal_places=8, default=200.0)
    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"VIP Upgrade for {self.user.username} - {self.status}"

