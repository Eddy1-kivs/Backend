from rest_framework import serializers
from api.models import Notification
from django.contrib.humanize.templatetags.humanize import naturaltime

class NotificationSerializer(serializers.ModelSerializer):
    timestamp_humanized = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = '__all__'

    def get_timestamp_humanized(self, obj): 
        return naturaltime(obj.timestamp)
