from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    register_user, UserMeView, get_referrals, verify_email, verify_phone,
    password_reset_request, password_reset_confirm, enable_2fa, verify_2fa,
    CustomTokenObtainPairView, withdraw_user_profit, VIPUpgradeViewSet,
    upload_profile_picture
)

urlpatterns = [
    path('auth/register/', register_user, name='auth_register'),
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    path('auth/verify-email/', verify_email, name='verify_email'),
    path('auth/verify-phone/', verify_phone, name='verify_phone'),
    
    path('auth/password-reset/', password_reset_request, name='password_reset'),
    path('auth/password-reset/confirm/', password_reset_confirm, name='password_reset_confirm'),
    
    path('auth/2fa/enable/', enable_2fa, name='enable_2fa'),
    path('auth/2fa/verify/', verify_2fa, name='verify_2fa'),
    
    path('users/me/', UserMeView.as_view(), name='user_me'),
    path('users/me/profile-picture/', upload_profile_picture, name='upload_profile_picture'),
    path('users/me/referrals/', get_referrals, name='user_referrals'),
    path('users/me/withdraw-profit/', withdraw_user_profit, name='user_withdraw_profit'),
    path('users/vip-upgrade/', VIPUpgradeViewSet.as_view({'post': 'create', 'get': 'list'}), name='vip_upgrade'),
]

