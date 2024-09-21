from rest_framework import serializers 
from api.models import Messaging, UploadFile, CustomUser
from django.utils import timezone


class UploadFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadFile
        fields = ['id', 'file', 'uploaded_at']
        
        
class CustomUserSerializer(serializers.ModelSerializer):
    class Meta: 
        model = CustomUser
        fields = ['id', 'username', 'profile_image']

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)
    sender_profile_image = serializers.ImageField(source='sender.profile_image', read_only=True)
    receiver_username = serializers.CharField(source='receiver.username', read_only=True)
    receiver_profile_image = serializers.ImageField(source='receiver.profile_image', read_only=True)
    partner_username = serializers.SerializerMethodField()
    partner_profile_image = serializers.SerializerMethodField()
    timestamp = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.%fZ", read_only=True)  # Include raw timestamp
    unread_count = serializers.SerializerMethodField()
    is_incoming = serializers.SerializerMethodField()
    files = UploadFileSerializer(many=True, read_only=True)

    class Meta:
        model = Messaging
        fields = ['id', 'sender', 'sender_username', 'sender_profile_image', 'receiver', 'receiver_username', 'receiver_profile_image', 'partner_username', 'partner_profile_image', 'message', 'is_read', 'timestamp', 'unread_count', 'is_incoming', 'files']
 
    def get_partner_username(self, obj):
        user = self.context.get('request', None).user
        if user:
            if obj.sender == user:
                return obj.receiver.username
            else:
                return obj.sender.username
        return None

    def get_partner_profile_image(self, obj):
        user = self.context.get('request', None).user
        if user:
            if obj.sender == user:
                return obj.receiver.profile_image
            else:
                return obj.sender.profile_image
        return None

    def get_unread_count(self, obj):
        user = self.context.get('request', None).user
        if user:
            if obj.sender == user:
                return Messaging.objects.filter(sender=obj.receiver, receiver=obj.sender, is_read=False).count()
            else:
                return Messaging.objects.filter(sender=obj.sender, receiver=obj.receiver, is_read=False).count()
        return 0

    def get_is_incoming(self, obj):
        user = self.context.get('request', None).user
        return user != obj.sender
