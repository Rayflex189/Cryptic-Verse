from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from admin_panel.models import Admin, AuditLog

User = get_user_model()

class AdminUserDeleteTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = Admin.objects.create(
            email="admin@example.com",
            full_name="Super Admin",
            role="SUPER_ADMIN",
            is_active=True
        )
        self.admin.set_password("adminpass")
        self.admin.save()

        self.user = User.objects.create_user(
            username="user_to_delete",
            email="delete_me@example.com",
            password="userpass123",
            full_name="Delete Me"
        )
        
        # Authenticate admin by adding token headers manually
        from admin_panel.views import get_tokens_for_admin
        tokens = get_tokens_for_admin(self.admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def test_delete_user_succeeds(self):
        """Test admin can delete a user and it creates an audit log entry."""
        url = f"/api/v1/admin/users/{self.user.id}/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user is deleted
        self.assertFalse(User.objects.filter(id=self.user.id).exists())
        
        # Verify audit log is created
        audit_log = AuditLog.objects.filter(action='DELETE_USER', entity_id=str(self.user.id)).first()
        self.assertIsNotNone(audit_log)
        self.assertEqual(audit_log.admin, self.admin)
        self.assertEqual(audit_log.old_values['username'], "user_to_delete")
