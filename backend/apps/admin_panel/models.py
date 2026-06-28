from django.db import models
from django.contrib.auth.hashers import make_password, check_password as django_check_password
from django.conf import settings

class Admin(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)   # hashed
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=20, choices=[('ADMIN', 'Admin'), ('SUPER_ADMIN', 'Super Admin')], default='ADMIN')
    permissions = models.JSONField(default=list)   # e.g., ["manage_users", "manage_deposits"]
    is_active = models.BooleanField(default=True)
    otp_secret = models.CharField(max_length=32, blank=True)
    is_2fa_enabled = models.BooleanField(default=False)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return django_check_password(raw_password, self.password)

    def __str__(self):
        return f"{self.full_name} ({self.role})"

class AuditLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    admin = models.ForeignKey(Admin, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)
    entity_type = models.CharField(max_length=50)
    entity_id = models.CharField(max_length=36, blank=True)
    old_values = models.JSONField(default=dict)
    new_values = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        actor = self.admin.full_name if self.admin else (self.user.username if self.user else "System")
        return f"{actor} performed {self.action} on {self.entity_type} #{self.entity_id}"

class WebsiteSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.JSONField()
    category = models.CharField(max_length=50)   # 'general', 'security', 'email'
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key
