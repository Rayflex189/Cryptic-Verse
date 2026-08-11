from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.html import format_html
from django.db import transaction
from django.utils import timezone
from .models import Withdrawal
from transactions.models import Transaction
from notifications.models import Notification

@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('transaction_code', 'user', 'amount', 'currency', 'method', 'status', 'created_at', 'contact_support_action')
    list_filter = ('method', 'status', 'currency', 'created_at')
    search_fields = ('transaction_code', 'user__username', 'user__email', 'address', 'confirmation_code')
    readonly_fields = ('transaction_code', 'confirmation_code', 'created_at', 'updated_at')
    actions = ['approve_withdrawals', 'reject_withdrawals', 'mark_pending']

    def contact_support_action(self, obj):
        return format_html(
            '<a class="button" style="background-color: #06b6d4; color: #000; font-weight: bold; padding: 4px 8px; border-radius: 4px;" href="{}">Contact Support</a>',
            f"/django-admin/withdrawals/withdrawal/{obj.id}/verification/"
        )
    contact_support_action.short_description = "Verification / Support"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/verification/', self.admin_site.admin_view(self.verification_view), name='withdrawal_verification'),
        ]
        return custom_urls + urls

    def verification_view(self, request, object_id):
        withdrawal = get_object_or_404(Withdrawal, pk=object_id)
        
        if request.method == 'POST':
            action_type = request.POST.get('action_type')
            admin_notes = request.POST.get('admin_notes', '')

            if action_type == 'APPROVE':
                with transaction.atomic():
                    withdrawal.status = 'COMPLETED'
                    withdrawal.admin_notes = admin_notes
                    withdrawal.processed_at = timezone.now()
                    withdrawal.save()

                    # Deduct locked balance
                    wallet = withdrawal.wallet
                    if wallet.locked_balance >= withdrawal.amount:
                        wallet.locked_balance -= withdrawal.amount
                    else:
                        wallet.locked_balance = 0
                    wallet.save()

                    # Create completed transaction record
                    Transaction.objects.create(
                        user=withdrawal.user,
                        wallet=wallet,
                        type='WITHDRAWAL',
                        amount=-withdrawal.amount,
                        currency=withdrawal.currency,
                        description=f"Withdrawal {withdrawal.transaction_code} approved via {withdrawal.get_method_display()}",
                        reference_id=str(withdrawal.id),
                        status='COMPLETED'
                    )

                    # Notify user
                    Notification.objects.create(
                        user=withdrawal.user,
                        title="Withdrawal Approved",
                        message=f"Your withdrawal {withdrawal.transaction_code} of ${withdrawal.amount} {withdrawal.currency} has been approved and processed.",
                        type="SUCCESS"
                    )

                messages.success(request, f"Withdrawal {withdrawal.transaction_code} has been APPROVED successfully.")
                return redirect('/django-admin/withdrawals/withdrawal/')

            elif action_type == 'REJECT':
                with transaction.atomic():
                    withdrawal.status = 'REJECTED'
                    withdrawal.admin_notes = admin_notes
                    withdrawal.processed_at = timezone.now()
                    withdrawal.save()

                    # Refund locked balance back to available balance
                    wallet = withdrawal.wallet
                    if wallet.locked_balance >= withdrawal.amount:
                        wallet.locked_balance -= withdrawal.amount
                    else:
                        wallet.locked_balance = 0
                    wallet.balance += withdrawal.amount
                    wallet.save()

                    # Notify user
                    Notification.objects.create(
                        user=withdrawal.user,
                        title="Withdrawal Rejected",
                        message=f"Your withdrawal {withdrawal.transaction_code} of ${withdrawal.amount} {withdrawal.currency} was rejected. Reason: {admin_notes or 'Administrative decision'}.",
                        type="ERROR"
                    )

                messages.warning(request, f"Withdrawal {withdrawal.transaction_code} has been REJECTED and funds refunded to user.")
                return redirect('/django-admin/withdrawals/withdrawal/')

            elif action_type == 'PENDING':
                withdrawal.status = 'PENDING'
                withdrawal.admin_notes = admin_notes
                withdrawal.save()
                messages.info(request, f"Withdrawal {withdrawal.transaction_code} marked as PENDING.")
                return redirect('/django-admin/withdrawals/withdrawal/')

        context = {
            **self.admin_site.each_context(request),
            'withdrawal': withdrawal,
            'title': f'Support Verification - Withdrawal {withdrawal.transaction_code}',
            'opts': self.model._meta,
        }
        return render(request, 'admin/withdrawals/verification.html', context)

    @admin.action(description="Approve selected withdrawals")
    def approve_withdrawals(self, request, queryset):
        count = 0
        for w in queryset.filter(status__in=['PENDING', 'CONFIRMED', 'PROCESSING']):
            with transaction.atomic():
                w.status = 'COMPLETED'
                w.processed_at = timezone.now()
                w.save()

                wallet = w.wallet
                if wallet.locked_balance >= w.amount:
                    wallet.locked_balance -= w.amount
                else:
                    wallet.locked_balance = 0
                wallet.save()

                Transaction.objects.create(
                    user=w.user,
                    wallet=wallet,
                    type='WITHDRAWAL',
                    amount=-w.amount,
                    currency=w.currency,
                    description=f"Withdrawal {w.transaction_code} approved",
                    reference_id=str(w.id),
                    status='COMPLETED'
                )

                Notification.objects.create(
                    user=w.user,
                    title="Withdrawal Approved",
                    message=f"Your withdrawal {w.transaction_code} of ${w.amount} {w.currency} has been approved.",
                    type="SUCCESS"
                )
            count += 1
        messages.success(request, f"Approved {count} withdrawal(s).")

    @admin.action(description="Reject selected withdrawals")
    def reject_withdrawals(self, request, queryset):
        count = 0
        for w in queryset.filter(status__in=['PENDING', 'CONFIRMED', 'PROCESSING']):
            with transaction.atomic():
                w.status = 'REJECTED'
                w.processed_at = timezone.now()
                w.save()

                wallet = w.wallet
                if wallet.locked_balance >= w.amount:
                    wallet.locked_balance -= w.amount
                else:
                    wallet.locked_balance = 0
                wallet.balance += w.amount
                wallet.save()

                Notification.objects.create(
                    user=w.user,
                    title="Withdrawal Rejected",
                    message=f"Your withdrawal {w.transaction_code} was rejected and balance refunded.",
                    type="ERROR"
                )
            count += 1
        messages.warning(request, f"Rejected {count} withdrawal(s).")

    @admin.action(description="Mark selected withdrawals as Pending")
    def mark_pending(self, request, queryset):
        updated = queryset.update(status='PENDING')
        messages.info(request, f"Marked {updated} withdrawal(s) as PENDING.")
