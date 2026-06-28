from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WalletViewSet, AdminWalletAddressViewSet

router = DefaultRouter()
router.register(r'wallets', WalletViewSet, basename='wallet')
router.register(r'admin/wallet-addresses', AdminWalletAddressViewSet, basename='admin-wallet-address')

urlpatterns = [
    path('', include(router.urls)),
]
