from rest_framework import viewsets, permissions, views
from rest_framework.response import Response
from .models import KYCDocument
from .serializers import KYCDocumentSerializer

class KYCDocumentViewSet(viewsets.ModelViewSet):
    serializer_class = KYCDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return KYCDocument.objects.filter(user=self.request.user)

class KYCStatusView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        docs = KYCDocument.objects.filter(user=user)
        docs_serialized = KYCDocumentSerializer(docs, many=True)
        return Response({
            'kyc_status': user.kyc_status,
            'kyc_level': user.kyc_level,
            'documents': docs_serialized.data
        })
