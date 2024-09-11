from rest_framework import serializers
from api.models import Review
from django.contrib.humanize.templatetags.humanize import naturaltime

from django.utils import timezone


class ReviewSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    reviewer_username = serializers.ReadOnlyField(source='reviewer.username')
    job_title = serializers.ReadOnlyField(source='job.title')

    class Meta:
        model = Review
        fields = ['id', 'reviewer', 'reviewer_username', 'recipient', 'job', 'job_title', 'rating', 'comment', 'created_at']

    def get_created_at(self, obj): 
        return naturaltime(obj.created_at)
