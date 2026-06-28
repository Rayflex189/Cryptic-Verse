from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Withdrawal
from .serializers import WithdrawalSerializer
from transactions.models import Transaction

class WithdrawalViewSet(viewsets.ModelViewSet):
    serializer_class = WithdrawalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Withdrawal.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='confirm')
    def confirm_withdrawal(self, request, pk=None):
        withdrawal = self.get_object()
        code = request.data.get('code')
        
        if withdrawal.status != 'PENDING':
            return Response({'error': 'Withdrawal has already been processed or confirmed.'}, status=status.HTTP_400_BAD_REQUEST)
            
        if withdrawal.confirmation_code == code:
            with transaction.atomic():
                withdrawal.status = 'CONFIRMED'
                withdrawal.save()
                
                # Create the pending withdrawal transaction
                Transaction.objects.create(
                    user=withdrawal.user,
                    wallet=withdrawal.wallet,
                    type='WITHDRAWAL',
                    amount=withdrawal.amount,
                    currency=withdrawal.currency,
                    description="in 5 working days it reflects in recievers account",
                    reference_id=str(withdrawal.id),
                    status='PENDING'
                )
            return Response({'message': 'Withdrawal confirmed successfully.'})
            
        return Response({'error': 'Invalid confirmation code.'}, status=status.HTTP_400_BAD_REQUEST)

