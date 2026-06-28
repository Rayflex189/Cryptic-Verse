from django.db import models
from django.conf import settings
from core.encryption import encrypt_value, decrypt_value

class KYCDocument(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='kyc_documents')
    document_type = models.CharField(
        max_length=20,
        choices=[
            ('ID_CARD', 'ID Card'),
            ('PASSPORT', 'Passport'),
            ('DRIVERS_LICENSE', "Driver's License"),
            ('PROOF_OF_ADDRESS', 'Proof of Address'),
            ('SELFIE', 'Selfie'),
            ('SSN', 'SSN')
        ]
    )
    document_url = models.URLField(max_length=500)   # stored in Supabase storage or local
    document_number_encrypted = models.CharField(max_length=255, blank=True, db_column='document_number')   # encrypted
    issued_country = models.CharField(max_length=100, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')],
        default='PENDING'
    )
    reviewed_by = models.ForeignKey('admin_panel.Admin', on_delete=models.SET_NULL, null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def document_number(self):
        return decrypt_value(self.document_number_encrypted)

    @document_number.setter
    def document_number(self, value):
        self.document_number_encrypted = encrypt_value(value)

    def __str__(self):
        return f"{self.user.username}'s {self.document_type} document"
