from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import VIPLevel, VIPUpgradeRequest

User = get_user_model()

class VIPLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = VIPLevel
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    vip_level_details = VIPLevelSerializer(source='vip_level', read_only=True)
    ssn = serializers.CharField(write_only=True, required=False)
    active_investment = serializers.ReadOnlyField()
    profit_accrued = serializers.ReadOnlyField()
    referral_bonus = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'full_name', 'date_of_birth',
            'address', 'city', 'state', 'country', 'zip_code', 'ssn', 'profile_picture',
            'is_email_verified', 'is_phone_verified', 'kyc_status', 'kyc_level',
            'vip_level', 'vip_level_details', 'referral_code', 'balance', 'profit_balance',
            'is_frozen', 'is_2fa_enabled', 'created_at', 'updated_at',
            'active_investment', 'profit_accrued', 'referral_bonus'
        ]
        read_only_fields = [
            'id', 'username', 'is_email_verified', 'is_phone_verified',
            'kyc_status', 'kyc_level', 'vip_level', 'referral_code',
            'balance', 'profit_balance', 'is_frozen', 'is_2fa_enabled', 'created_at', 'updated_at'
        ]

class AdminUserSerializer(serializers.ModelSerializer):
    vip_level_details = VIPLevelSerializer(source='vip_level', read_only=True)
    active_investment = serializers.ReadOnlyField()
    profit_accrued = serializers.ReadOnlyField()
    referral_bonus = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'full_name', 'date_of_birth',
            'address', 'city', 'state', 'country', 'zip_code', 'profile_picture',
            'is_email_verified', 'is_phone_verified', 'kyc_status', 'kyc_level',
            'vip_level', 'vip_level_details', 'referral_code', 'balance', 'profit_balance',
            'is_frozen', 'is_2fa_enabled', 'created_at', 'updated_at',
            'active_investment', 'profit_accrued', 'referral_bonus',
            'active_investment_override', 'profit_accrued_override', 'referral_bonus_override'
        ]
        # balance, profit_balance, is_frozen, kyc_status, vip_level etc are writable in admin serializer
        read_only_fields = [
            'id', 'username', 'referral_code', 'created_at', 'updated_at'
        ]


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if not self.user.is_email_verified:
            raise serializers.ValidationError({"detail": "Please verify your email address before logging in."})
        return data


    def create(self, validated_data):
        ssn = validated_data.pop('ssn', None)
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        if ssn:
            user.ssn = ssn
        user.save()
        return user

    def update(self, instance, validated_data):
        ssn = validated_data.pop('ssn', None)
        if ssn:
            instance.ssn = ssn
        return super().update(instance, validated_data)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    referral_code = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'full_name', 'phone', 'referral_code']

    def create(self, validated_data):
        referral_code = validated_data.pop('referral_code', None)
        referred_by = None
        if referral_code:
            try:
                referred_by = User.objects.get(referral_code=referral_code)
            except User.DoesNotExist:
                pass
        
        password = validated_data.pop('password')
        user = User(**validated_data, referred_by=referred_by)
        user.set_password(password)
        user.save()
        return user

class VIPUpgradeRequestSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = VIPUpgradeRequest
        fields = '__all__'
        read_only_fields = ['id', 'user', 'amount', 'status', 'created_at', 'updated_at']


