from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.core.management import call_command
from wallets.models import Wallet
from transactions.models import Transaction
from admin_panel.models import WebsiteSetting
from investments.models import InvestmentPlan, Investment

User = get_user_model()

class AutomatedProfitDistributionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="investor",
            email="investor@example.com",
            password="password123",
            full_name="Plan Investor"
        )
        self.wallet = Wallet.objects.get(user=self.user, currency="USDT")
        self.wallet.balance = 5000.00
        self.wallet.save()

        # Seed VIP Level
        from users.models import VIPLevel
        VIPLevel.objects.get_or_create(level=1, defaults={'name': 'VIP Level 1', 'min_balance': 0, 'benefits': []})

        self.plan = InvestmentPlan.objects.create(
            name="Alpha Yield",
            min_deposit=100.00,
            max_deposit=10000.00,
            daily_profit_percent=1.00,  # 1% per day
            duration_days=30,
            compounding=False
        )

    def test_investment_schedule_calculation(self):
        """Test that schedule calculations (expected payouts, amount per payout) are computed on save."""
        now = timezone.now()
        inv = Investment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=1000.00,
            currency="USDT",
            expected_profit=30,  # 30% expected profit
            expected_profit_type="PERCENT",
            distribution_frequency="DAILY",
            start_date=now
        )
        
        # Total profit is 30% of 1000 = 300 USDT.
        # Daily distribution frequency over 30 days = 30 payouts.
        # Expected payout = 300 / 30 = 10 USDT per day.
        self.assertEqual(inv.total_payouts_expected, 30)
        self.assertEqual(inv.amount_per_payout, 10.00)
        self.assertAlmostEqual(inv.end_date, now + timedelta(days=30), delta=timedelta(seconds=5))
        self.assertAlmostEqual(inv.next_payout_at, now + timedelta(days=1), delta=timedelta(seconds=5))

    def test_distribute_profits_command_credits_wallet(self):
        """Test that the distribute_profits command credits the user profit wallet when next_payout_at has arrived."""
        now = timezone.now()
        # Set start_date in the past so next_payout_at is now/past
        start_date = now - timedelta(days=1)
        
        inv = Investment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=1000.00,
            currency="USDT",
            expected_profit=30.00,
            expected_profit_type="PERCENT",
            distribution_frequency="DAILY",
            start_date=start_date
        )
        # Next payout was set to: start_date + 1 day = now
        # Force next_payout_at to be slightly in the past to guarantee execution
        inv.next_payout_at = now - timedelta(minutes=5)
        inv.save()

        # Run command
        call_command('distribute_profits')

        # Check that user USDT wallet balance increased by 10 USDT
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 5010.00)

        # Check investment profit accrued and payouts made
        inv.refresh_from_db()
        self.assertEqual(inv.profit_accrued, 10.00)
        self.assertEqual(inv.payouts_made, 1)

        # Verify transaction log created
        tx = Transaction.objects.filter(user=self.user, type='PROFIT').first()
        self.assertIsNotNone(tx)
        self.assertEqual(tx.amount, 10.00)

    def test_global_automation_killswitch(self):
        """Test that global automation switch stops automated distributions."""
        now = timezone.now()
        start_date = now - timedelta(days=1)

        # Create global switch setting set to False
        WebsiteSetting.objects.create(
            key="global_profit_distribution_enabled",
            value=False,
            category="general"
        )

        inv = Investment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=1000.00,
            currency="USDT",
            expected_profit=30.00,
            expected_profit_type="PERCENT",
            distribution_frequency="DAILY",
            start_date=start_date
        )
        inv.next_payout_at = now - timedelta(minutes=5)
        inv.save()

        call_command('distribute_profits')

        # Balance should remain at 5000 (no profit credited)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 5000.00)

    def test_paused_investment_skipped(self):
        """Test that paused investments do not receive distributions."""
        now = timezone.now()
        start_date = now - timedelta(days=1)

        inv = Investment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=1000.00,
            currency="USDT",
            expected_profit=30.00,
            expected_profit_type="PERCENT",
            distribution_frequency="DAILY",
            start_date=start_date,
            is_paused=True
        )
        inv.next_payout_at = now - timedelta(minutes=5)
        inv.save()

        call_command('distribute_profits')

        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, 5000.00)
