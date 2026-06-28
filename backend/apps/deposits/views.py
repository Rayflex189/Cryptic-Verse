from rest_framework import viewsets, permissions, parsers
from .models import Deposit
from .serializers import DepositSerializer

class DepositViewSet(viewsets.ModelViewSet):
    serializer_class = DepositSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]

    def get_queryset(self):
        return Deposit.objects.filter(user=self.request.user)
