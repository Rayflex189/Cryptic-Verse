from rest_framework import serializers
from .models import KYCDocument

class KYCDocumentSerializer(serializers.ModelSerializer):
    document_number = serializers.CharField(required=True)

    class Meta:
        model = KYCDocument
        fields = '__all__'
        read_only_fields = ['id', 'user', 'status', 'reviewed_by', 'rejection_reason', 'reviewed_at', 'created_at', 'updated_at']

    def create(self, validated_data):
        user = self.context['request'].user
        document_number = validated_data.pop('document_number')
        kyc_doc = KYCDocument.objects.create(user=user, **validated_data)
        kyc_doc.document_number = document_number
        kyc_doc.save()
        return kyc_doc
