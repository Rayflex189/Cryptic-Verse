from rest_framework import serializers
from django.db import transaction
from .models import InvestmentPlan, Investment
from wallets.models import Wallet

class InvestmentPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvestmentPlan
        fields = '__all__'

class InvestmentSerializer(serializers.ModelSerializer):
    plan_details = InvestmentPlanSerializer(source='plan', read_only=True)

    class Meta:
        model = Investment
        fields = '__all__'
        read_only_fields = ['id', 'user', 'start_date', 'end_date', 'status', 'profit_accrued', 'created_at', 'updated_at']

    def validate(self, data):
        plan = data.get('plan')
        amount = data.get('amount')
        currency = data.get('currency')
        user = self.context['request'].user

        if amount < plan.min_deposit or amount > plan.max_deposit:
            raise serializers.ValidationError(
                f"Amount must be between {plan.min_deposit} and {plan.max_deposit} for {plan.name}."
            )

        try:
            wallet = Wallet.objects.get(user=user, currency=currency)
        except Wallet.DoesNotExist:
            raise serializers.ValidationError(f"You do not have a {currency} wallet.")

        if wallet.balance < amount:
            raise serializers.ValidationError(f"Insufficient wallet balance. Available: {wallet.balance} {currency}")

        return data

    def create(self, validated_data):
        user = self.context['request'].user
        amount = validated_data.get('amount')
        currency = validated_data.get('currency')
        wallet = Wallet.objects.get(user=user, currency=currency)

        with transaction.atomic():
            wallet.balance -= amount
            wallet.save()

            investment = Investment.objects.create(
                user=user,
                **validated_data
            )
        return investment
