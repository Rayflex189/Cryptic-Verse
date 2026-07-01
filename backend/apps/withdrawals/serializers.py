from rest_framework import serializers
from django.db import transaction
from .models import Withdrawal
from wallets.models import Wallet

class WithdrawalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Withdrawal
        fields = '__all__'
        read_only_fields = ['id', 'user', 'wallet', 'status', 'confirmation_code', 'approved_by', 'admin_notes', 'processed_at', 'created_at', 'updated_at']

    def validate(self, data):
        user = self.context['request'].user
        currency = data.get('currency')
        amount = data.get('amount')
        
        lookup_currency = 'USDT' if currency == 'BANK' else currency
        
        try:
            wallet = Wallet.objects.get(user=user, currency=lookup_currency)
        except Wallet.DoesNotExist:
            raise serializers.ValidationError(f"You do not have a {lookup_currency} wallet.")

        if wallet.balance < amount:
            raise serializers.ValidationError(f"Insufficient funds in your {lookup_currency} wallet. Available: {wallet.balance}")

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        currency = validated_data.get('currency')
        amount = validated_data.get('amount')
        
        lookup_currency = 'USDT' if currency == 'BANK' else currency
        wallet = Wallet.objects.get(user=user, currency=lookup_currency)

        with transaction.atomic():
            wallet.balance -= amount
            wallet.locked_balance += amount
            wallet.save()

            withdrawal = Withdrawal.objects.create(
                user=user,
                wallet=wallet,
                **validated_data
            )
        return withdrawal
