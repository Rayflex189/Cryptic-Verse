from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Wallet, AdminWalletAddress
from .serializers import WalletSerializer, AdminWalletAddressSerializer
from admin_panel.permissions import IsAdminUserToken

class WalletViewSet(viewsets.ModelViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Wallet.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='create')
    def create_wallet(self, request):
        currency = request.data.get('currency')
        if not currency:
            return Response({'error': 'Currency is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        wallet, created = Wallet.objects.get_or_create(user=request.user, currency=currency)
        serializer = self.get_serializer(wallet)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class AdminWalletAddressViewSet(viewsets.ModelViewSet):
    authentication_classes = ()
    serializer_class = AdminWalletAddressSerializer
    permission_classes = [IsAdminUserToken]
    queryset = AdminWalletAddress.objects.all()
