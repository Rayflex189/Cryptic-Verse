from rest_framework import serializers
from .models import SupportTicket, TicketMessage
import os

ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

def validate_image_file(file_obj):
    if not file_obj:
        return
    ext = os.path.splitext(file_obj.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise serializers.ValidationError(
            f"Unsupported image type '{ext}'. Allowed image formats are JPG, JPEG, PNG, WEBP, and GIF."
        )
    if file_obj.size > MAX_IMAGE_SIZE_BYTES:
        raise serializers.ValidationError("Attached image exceeds the maximum allowed size of 10 MB.")

class TicketMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = TicketMessage
        fields = ['id', 'ticket', 'sender', 'sender_name', 'sender_username', 'message', 'attachment', 'is_admin', 'created_at']
        read_only_fields = ['id', 'ticket', 'sender', 'is_admin', 'created_at']

    def validate(self, attrs):
        message = attrs.get('message', '').strip()
        attachment = attrs.get('attachment')
        if not message and not attachment:
            raise serializers.ValidationError("A message text or an image attachment is required.")
        if attachment:
            validate_image_file(attachment)
        return attrs

class SupportTicketSerializer(serializers.ModelSerializer):
    messages = TicketMessageSerializer(many=True, read_only=True)
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id', 'user', 'user_full_name', 'user_username', 'subject', 'message',
            'initial_attachment', 'status', 'priority', 'assigned_to',
            'resolved_at', 'created_at', 'updated_at', 'messages'
        ]
        read_only_fields = ['id', 'user', 'status', 'assigned_to', 'resolved_at', 'created_at', 'updated_at']

    def validate_initial_attachment(self, value):
        if value:
            validate_image_file(value)
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        ticket = SupportTicket.objects.create(user=user, **validated_data)
        # Create initial message in ticket thread
        TicketMessage.objects.create(
            ticket=ticket,
            sender=user,
            message=ticket.message,
            attachment=ticket.initial_attachment,
            is_admin=False
        )
        return ticket
