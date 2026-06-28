from rest_framework import serializers
from .models import Wallet, AdminWalletAddress

class AdminWalletAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminWalletAddress
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class WalletSerializer(serializers.ModelSerializer):
    address = serializers.ReadOnlyField()

    class Meta:
        model = Wallet
        fields = '__all__'
        read_only_fields = ['id', 'user', 'balance', 'locked_balance', 'created_at', 'updated_at']
