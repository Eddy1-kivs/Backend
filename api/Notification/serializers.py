from rest_framework import serializers
from api.models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'message', 'icon', 'is_read', 'timestamp', 'url']
