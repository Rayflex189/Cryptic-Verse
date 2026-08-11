from rest_framework import serializers
from django.db import transaction
from .models import Withdrawal
from wallets.models import Wallet

class WithdrawalSerializer(serializers.ModelSerializer):
    address = serializers.CharField(required=False, allow_blank=True, default='')
    method = serializers.ChoiceField(
        choices=[('BANK', 'Bank Transfer'), ('CRYPTO', 'Cryptocurrency'), ('PAYPAL', 'PayPal')],
        default='CRYPTO'
    )
    details = serializers.JSONField(required=False, default=dict)

    class Meta:
        model = Withdrawal
        fields = '__all__'
        read_only_fields = [
            'id', 'user', 'wallet', 'status', 'transaction_code',
            'confirmation_code', 'approved_by', 'admin_notes',
            'processed_at', 'created_at', 'updated_at'
        ]

    def validate(self, data):
        user = self.context['request'].user
        currency = data.get('currency', 'USDT')
        amount = data.get('amount')
        method = data.get('method', 'CRYPTO')
        details = data.get('details', {})

        if not amount or amount <= 0:
            raise serializers.ValidationError({"amount": "Please enter a valid positive withdrawal amount."})

        # Method validation
        if method == 'BANK':
            required_bank_fields = ['bank_name', 'account_name', 'account_number', 'country']
            missing = [f for f in required_bank_fields if not details.get(f)]
            if missing:
                raise serializers.ValidationError({
                    "details": f"Missing required bank details: {', '.join(missing)}"
                })
        elif method == 'CRYPTO':
            wallet_addr = details.get('wallet_address') or data.get('address')
            if not wallet_addr:
                raise serializers.ValidationError({
                    "details": "Cryptocurrency destination wallet address is required."
                })
        elif method == 'PAYPAL':
            if not details.get('paypal_email'):
                raise serializers.ValidationError({
                    "details": "PayPal email address is required."
                })

        # Determine wallet currency to deduct
        lookup_currency = currency if currency in ['USDT', 'BTC', 'ETH', 'BNB', 'SOL'] else 'USDT'

        try:
            wallet = Wallet.objects.get(user=user, currency=lookup_currency)
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(user=user, currency=lookup_currency, balance=0)

        if wallet.balance < amount:
            raise serializers.ValidationError({
                "amount": f"Insufficient funds in your {lookup_currency} wallet. Available balance: ${float(wallet.balance):.2f}"
            })

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        currency = validated_data.get('currency', 'USDT')
        amount = validated_data.get('amount')
        method = validated_data.get('method', 'CRYPTO')
        details = validated_data.get('details', {})
        address = validated_data.get('address', '')

        # Build clean address string if empty
        if not address:
            if method == 'BANK':
                address = f"Bank: {details.get('bank_name')} | Acc: {details.get('account_number')} ({details.get('account_name')})"
            elif method == 'CRYPTO':
                address = f"{details.get('crypto_coin', currency)} ({details.get('crypto_network', 'Native')}): {details.get('wallet_address')}"
            elif method == 'PAYPAL':
                address = f"PayPal: {details.get('paypal_email')}"

        lookup_currency = currency if currency in ['USDT', 'BTC', 'ETH', 'BNB', 'SOL'] else 'USDT'
        wallet = Wallet.objects.get(user=user, currency=lookup_currency)

        with transaction.atomic():
            wallet.balance -= amount
            wallet.locked_balance += amount
            wallet.save()

            withdrawal = Withdrawal.objects.create(
                user=user,
                wallet=wallet,
                amount=amount,
                currency=currency,
                method=method,
                details=details,
                address=address
            )
        return withdrawal
