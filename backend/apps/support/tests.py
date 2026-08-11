import io
from PIL import Image
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status
from support.models import SupportTicket, TicketMessage
from admin_panel.models import Admin

User = get_user_model()

def generate_dummy_image(name="test.png", ext="PNG", size=(100, 100), color=(0, 255, 0)):
    file_obj = io.BytesIO()
    img = Image.new('RGB', size, color=color)
    img.save(file_obj, ext)
    file_obj.seek(0)
    return SimpleUploadedFile(name, file_obj.read(), content_type=f"image/{ext.lower()}")

class SupportTicketImageMessagingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="support_user",
            email="support_user@example.com",
            password="password123",
            full_name="Support User",
            is_email_verified=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        from django.contrib.auth.hashers import make_password
        self.admin_obj = Admin.objects.create(
            email="admin_op@example.com",
            password=make_password("adminpassword123"),
            full_name="Admin Operator",
            role='SUPER_ADMIN'
        )
        self.admin_client = APIClient()
        token_res = self.admin_client.post('/api/v1/admin/auth/login/', {
            'email': 'admin_op@example.com',
            'password': 'adminpassword123'
        }, format='json')
        self.admin_token = token_res.data['tokens']['access']
        self.admin_client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.admin_token}')

    def test_user_create_ticket_with_image_attachment(self):
        """Test user creates a support ticket with text and initial image attachment."""
        dummy_img = generate_dummy_image("ticket_proof.png")
        url = '/api/v1/support/tickets/'
        data = {
            'subject': 'Deposit proof inquiry',
            'message': 'Please verify my attached deposit screenshot.',
            'priority': 'HIGH',
            'initial_attachment': dummy_img
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        
        ticket = SupportTicket.objects.get(id=response.data['id'])
        self.assertEqual(ticket.subject, 'Deposit proof inquiry')
        self.assertIsNotNone(ticket.initial_attachment)
        
        # Verify initial TicketMessage was created with attachment
        initial_msg = ticket.messages.first()
        self.assertIsNotNone(initial_msg)
        self.assertIsNotNone(initial_msg.attachment)

    def test_user_send_chat_reply_with_image(self):
        """Test user sends a chat message with image attachment."""
        ticket = SupportTicket.objects.create(
            user=self.user,
            subject='Wallet issue',
            message='Need help updating my address.'
        )
        dummy_img = generate_dummy_image("wallet_error.jpeg", "JPEG")
        url = f'/api/v1/support/tickets/{ticket.id}/messages/'
        data = {
            'message': 'Here is the screenshot of the error.',
            'attachment': dummy_img
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('attachment', response.data)
        self.assertIsNotNone(response.data['attachment'])

    def test_admin_reply_with_image_attachment(self):
        """Test admin replies to support ticket with text and image attachment via admin API."""
        ticket = SupportTicket.objects.create(
            user=self.user,
            subject='Account inquiry',
            message='Please clarify account rules.'
        )
        dummy_img = generate_dummy_image("admin_solution.webp", "WEBP")
        url = f'/api/v1/admin/support/tickets/{ticket.id}/reply/'
        data = {
            'message': 'Here is the screenshot showing your verified status.',
            'attachment': dummy_img,
            'status': 'RESOLVED'
        }
        response = self.admin_client.post(
            url,
            data,
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        ticket.refresh_from_db()
        self.assertEqual(ticket.status, 'RESOLVED')
        
        reply_msg = ticket.messages.filter(is_admin=True).first()
        self.assertIsNotNone(reply_msg)
        self.assertIsNotNone(reply_msg.attachment)

    def test_reject_invalid_image_extension(self):
        """Test that invalid non-image files like .exe or .pdf are rejected."""
        fake_exe = SimpleUploadedFile("malicious.exe", b"binary content", content_type="application/octet-stream")
        ticket = SupportTicket.objects.create(
            user=self.user,
            subject='Validation Test',
            message='Testing invalid file.'
        )
        url = f'/api/v1/support/tickets/{ticket.id}/messages/'
        response = self.client.post(url, {'attachment': fake_exe}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
