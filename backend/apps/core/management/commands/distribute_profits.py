from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from investments.models import Investment
from wallets.models import Wallet
from transactions.models import Transaction
from admin_panel.models import WebsiteSetting

class Command(BaseCommand):
    help = 'Processes automated investment scheduling, profit distribution, and plans maturity.'

    def handle(self, *args, **options):
        self.stdout.write('Processing investment scheduling and automated payouts...')
        now = timezone.now()

        # 1. Start investments automatically if start_date has arrived
        pending_investments = Investment.objects.filter(status='PENDING', start_date__lte=now)
        activated_count = 0
        for inv in pending_investments:
            inv.status = 'ACTIVE'
            inv.save()
            activated_count += 1
            self.stdout.write(f"Activated pending investment #{inv.id} for user {inv.user.username}")

        # 2. Check for matured active investments whose end_date has arrived
        matured_investments = Investment.objects.filter(status='ACTIVE', end_date__lte=now)
        matured_count = 0
        for inv in matured_investments:
            self.mature_investment(inv)
            matured_count += 1
            self.stdout.write(f"Matured active investment #{inv.id} for user {inv.user.username}")

        # 3. Check global profit distribution switch
        global_enabled = True
        setting = WebsiteSetting.objects.filter(key='global_profit_distribution_enabled').first()
        if setting:
            global_enabled = setting.value

        payout_count = 0
        if global_enabled:
            # Get active, automated, non-paused investments that are due for payout
            eligible_investments = Investment.objects.filter(
                status='ACTIVE',
                is_automated=True,
                is_paused=False,
                user__is_automation_enabled=True,
                next_payout_at__lte=now
            )
            for inv in eligible_investments:
                self.accrue_automated_profit(inv, now)
                payout_count += 1
        else:
            self.stdout.write(self.style.WARNING("Global profit distribution is currently disabled (kill-switch active)."))

        self.stdout.write(self.style.SUCCESS(
            f"Activated {activated_count} plans. Matured {matured_count} plans. Processed {payout_count} automated payouts."
        ))
        
        # 4. Accrue daily new account rewards
        self.stdout.write('Processing daily new account profits...')
        self.accrue_new_account_profits(now)

    def accrue_automated_profit(self, inv, now):
        payout_amount = inv.amount_per_payout

        with transaction.atomic():
            wallet, _ = Wallet.objects.get_or_create(user=inv.user, currency=inv.currency)
            wallet.balance += payout_amount
            wallet.save()

            # Record Ledger Transaction
            Transaction.objects.create(
                user=inv.user,
                wallet=wallet,
                type='PROFIT',
                amount=payout_amount,
                currency=inv.currency,
                description=f"Automated profit payout ({inv.payouts_made + 1}/{inv.total_payouts_expected}) for investment #{inv.id}",
                reference_id=str(inv.id),
                status='COMPLETED'
            )

            # Update investment trackers
            inv.profit_accrued += payout_amount
            inv.payouts_made += 1
            inv.last_payout_at = now
            
            # Calculate next payout date
            if inv.distribution_frequency == 'HOURLY':
                delta = timedelta(hours=1)
            elif inv.distribution_frequency == 'CUSTOM_6H':
                delta = timedelta(hours=6)
            elif inv.distribution_frequency == 'CUSTOM_12H':
                delta = timedelta(hours=12)
            elif inv.distribution_frequency == 'DAILY':
                delta = timedelta(days=1)
            elif inv.distribution_frequency == 'WEEKLY':
                delta = timedelta(weeks=1)
            else: # At maturity
                delta = inv.end_date - inv.start_date
                
            inv.next_payout_at = now + delta
            
            # Check if expected payouts are complete
            if inv.payouts_made >= inv.total_payouts_expected:
                inv.status = 'COMPLETED'
                # Return principal
                if not inv.auto_reinvest:
                    wallet.balance += inv.amount
                    wallet.save()
                    Transaction.objects.create(
                        user=inv.user,
                        wallet=wallet,
                        type='DEPOSIT',
                        amount=inv.amount,
                        currency=inv.currency,
                        description=f"Principal returned for matured Investment #{inv.id}",
                        reference_id=str(inv.id),
                        status='COMPLETED'
                    )
                else:
                    # Auto-reinvest
                    Investment.objects.create(
                        user=inv.user,
                        plan=inv.plan,
                        amount=inv.amount,
                        currency=inv.currency,
                        auto_reinvest=True
                    )
            
            inv.save()

    def mature_investment(self, inv):
        user = inv.user
        plan = inv.plan
        total_payout = inv.amount + inv.profit_accrued

        with transaction.atomic():
            wallet, _ = Wallet.objects.get_or_create(user=user, currency=inv.currency)
            
            if inv.auto_reinvest:
                if inv.profit_accrued > 0:
                    wallet.balance += inv.profit_accrued
                    wallet.save()
                    Transaction.objects.create(
                        user=user,
                        wallet=wallet,
                        type='PROFIT',
                        amount=inv.profit_accrued,
                        currency=inv.currency,
                        description=f"Accrued profit payout on maturity of Investment #{inv.id}",
                        reference_id=str(inv.id),
                        status='COMPLETED'
                    )

                inv.status = 'COMPLETED'
                inv.save()

                Investment.objects.create(
                    user=user,
                    plan=plan,
                    amount=inv.amount,
                    currency=inv.currency,
                    auto_reinvest=True
                )
            else:
                wallet.balance += total_payout
                wallet.save()

                if inv.profit_accrued > 0:
                    Transaction.objects.create(
                        user=user,
                        wallet=wallet,
                        type='PROFIT',
                        amount=inv.profit_accrued,
                        currency=inv.currency,
                        description=f"Accrued profit payout for matured Investment #{inv.id}",
                        reference_id=str(inv.id),
                        status='COMPLETED'
                    )
                Transaction.objects.create(
                    user=user,
                    wallet=wallet,
                    type='DEPOSIT',
                    amount=inv.amount,
                    currency=inv.currency,
                    description=f"Principal returned for matured Investment #{inv.id}",
                    reference_id=str(inv.id),
                    status='COMPLETED'
                )

                inv.status = 'COMPLETED'
                inv.save()

    def accrue_new_account_profits(self, now):
        from django.contrib.auth import get_user_model
        from django.db import models
        User = get_user_model()
        
        cutoff = now - timedelta(days=30)
        accrual_cutoff = now - timedelta(hours=23)
        
        new_users = User.objects.filter(
            created_at__gte=cutoff,
            is_active=True
        ).filter(
            models.Q(last_profit_accrual__isnull=True) | models.Q(last_profit_accrual__lte=accrual_cutoff)
        )
        
        accrued_users_count = 0
        for user in new_users:
            with transaction.atomic():
                user.profit_balance += 10
                user.last_profit_accrual = now
                user.save(update_fields=['profit_balance', 'last_profit_accrual'])
                
                wallet, _ = Wallet.objects.get_or_create(user=user, currency='USDT')
                
                Transaction.objects.create(
                    user=user,
                    wallet=wallet,
                    type='PROFIT',
                    amount=10.00,
                    currency='USDT',
                    description="Daily new account profit reward ($10 USD)",
                    status='COMPLETED'
                )
            accrued_users_count += 1
            
        self.stdout.write(self.style.SUCCESS(
            f'Accrued daily 10 USD profit for {accrued_users_count} new accounts.'
        ))

