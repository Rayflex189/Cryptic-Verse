from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from investments.models import Investment
from wallets.models import Wallet
from transactions.models import Transaction

class Command(BaseCommand):
    help = 'Distributes daily profits to active investments, matures completed plans, and handles auto-reinvestment.'

    def handle(self, *args, **options):
        self.stdout.write('Processing daily investment profits...')
        now = timezone.now()
        active_investments = Investment.objects.filter(status='ACTIVE')
        
        updated_count = 0
        matured_count = 0
        
        for inv in active_investments:
            # Check if investment has matured (end_date reached)
            if now >= inv.end_date:
                matured_count += 1
                self.mature_investment(inv)
            else:
                updated_count += 1
                self.accrue_profit(inv)

        self.stdout.write(self.style.SUCCESS(
            f'Accrued daily profit for {updated_count} active plans. Matured {matured_count} plans.'
        ))
        
        self.stdout.write('Processing daily new account profits...')
        self.accrue_new_account_profits(now)


    def accrue_profit(self, inv):
        # Calculate daily yield
        plan = inv.plan
        daily_profit = inv.amount * (plan.daily_profit_percent / 100)

        with transaction.atomic():
            if plan.compounding:
                # Add profit to the active principal amount for compound growth
                inv.amount += daily_profit
                inv.profit_accrued += daily_profit
            else:
                # Add profit to accrued pool
                inv.profit_accrued += daily_profit
            inv.save()

    def mature_investment(self, inv):
        # Mature the plan
        user = inv.user
        plan = inv.plan
        total_payout = inv.amount + inv.profit_accrued

        with transaction.atomic():
            wallet, _ = Wallet.objects.get_or_create(user=user, currency=inv.currency)
            
            if inv.auto_reinvest:
                # Payout accrued profits to wallet first
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

                # Re-create active investment with original amount
                inv.status = 'COMPLETED'
                inv.save()

                Investment.objects.create(
                    user=user,
                    plan=plan,
                    amount=inv.amount,
                    currency=inv.currency,
                    auto_reinvest=True
                )
                self.stdout.write(f"Auto-reinvested {inv.amount} {inv.currency} in {plan.name} for {user.username}")
            else:
                # Payout principal + accrued profits to user's wallet
                wallet.balance += total_payout
                wallet.save()

                # Record transaction
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
                self.stdout.write(f"Matured and paid out {total_payout} {inv.currency} to {user.username}")

    def accrue_new_account_profits(self, now):
        from django.contrib.auth import get_user_model
        from django.db import models
        User = get_user_model()
        
        # New account: registered within last 30 days
        cutoff = now - timedelta(days=30)
        # Accrual interval: 23 hours to allow minor scheduling deviations
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
                
                from wallets.models import Wallet
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

