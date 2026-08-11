from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from wallets.models import Wallet
from withdrawals.models import Withdrawal

User = get_user_model()

class WithdrawalBankTransferTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="withdraw_user",
            email="withdraw@example.com",
            password="password123",
            full_name="Withdraw User"
        )
        # Get automatically created USDT wallet and update balance
        self.wallet = Wallet.objects.get(user=self.user, currency="USDT")
        self.wallet.balance = 500.00
        self.wallet.save()
        self.client.force_authenticate(user=self.user)

    def test_bank_withdrawal_debits_usdt_wallet(self):
        """Test that initiating a BANK withdrawal correctly debits the USDT wallet and generates transaction code."""
        url = "/api/v1/withdrawals/"
        data = {
            "amount": 200.00,
            "currency": "USDT",
            "method": "BANK",
            "details": {
                "bank_name": "Chase Bank",
                "account_name": "John Doe",
                "account_number": "12345678",
                "country": "United States"
            }
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify USDT wallet balance is debited and locked balance is incremented
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 300.00)
        self.assertEqual(self.wallet.locked_balance, 200.00)

        # Verify withdrawal object is created with transaction_code and details
        withdrawal = Withdrawal.objects.filter(user=self.user).first()
        self.assertIsNotNone(withdrawal)
        self.assertTrue(withdrawal.transaction_code.startswith("PV-WD-"))
        self.assertEqual(withdrawal.method, "BANK")
        self.assertEqual(withdrawal.amount, 200.00)
        self.assertEqual(withdrawal.wallet, self.wallet)
        self.assertIn("Chase Bank", withdrawal.address)
