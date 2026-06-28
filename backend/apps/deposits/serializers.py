from rest_framework import serializers
from .models import Deposit
from wallets.models import Wallet

class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = '__all__'
        read_only_fields = ['id', 'user', 'status', 'admin_notes', 'confirmed_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user
        currency = validated_data.get('currency')
        wallet, _ = Wallet.objects.get_or_create(user=user, currency=currency)
        return Deposit.objects.create(user=user, wallet=wallet, **validated_data)
