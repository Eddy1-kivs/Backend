from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models import CustomUser,Notification, Proposal, Job, HiredFreelancer, JobSubmission, Revision, Invite
from .serializers import NotificationSerializer
from rest_framework.views import APIView
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.utils import timezone


logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    user.is_online = True
    user.save()

@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    user.is_online = False
    user.save()

class MarkNotificationAsRead(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
            notification.is_read = True
            notification.save()
            return Response({'status': 'notification marked as read'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

class MarkAllNotificationsAsRead(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        notifications = Notification.objects.filter(user=request.user, is_read=False)
        notifications.update(is_read=True)
        return Response({'status': 'all notifications marked as read'}, status=status.HTTP_200_OK)

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user, is_read=False).order_by('-timestamp')

    @action(detail=False, methods=['post'])
    def mark_as_read(self, request):
        notification_ids = request.data.get('ids', [])
        Notification.objects.filter(id__in=notification_ids, user=request.user).update(is_read=True)
        return Response({'status': 'notifications marked as read'}, status=status.HTTP_200_OK)

# def notify_user(user, message):
#     channel_layer = get_channel_layer()
#     async_to_sync(channel_layer.group_send)(
#         f'notifications_{user.id}',
#         {
#             'type': 'send_notification',
#             'message': message,
#         }
#     )

import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Proposal)
def create_proposal_notification(sender, instance, created, **kwargs):
    if created:
        freelancer_name = instance.freelancer.username
        message_for_client = f"Your job '{instance.job.title}' has received a new proposal from {freelancer_name}."
        url_for_client = f"/job-detail/{instance.job.id}/"
        logger.debug(f"Creating notification for client with URL: {url_for_client}")
        Notification.objects.create(user=instance.job.client, message=message_for_client, url=url_for_client)
        # notify_user(instance.job.client, {'message': message_for_client, 'url': url_for_client})

        message_for_freelancer = f"New proposal submitted for job: {instance.job.title}"
        url_for_freelancer = f"/proposal-view-page/{instance.id}/"
        logger.debug(f"Creating notification for freelancer with URL: {url_for_freelancer}")
        Notification.objects.create(user=instance.freelancer, message=message_for_freelancer, url=url_for_freelancer)
        # notify_user(instance.freelancer, {'message': message_for_freelancer, 'url': url_for_freelancer})
    else:
        dirty_fields = instance.get_dirty_fields()
        
        if 'viewed' in dirty_fields:
            message = f"Your proposal for job '{instance.job.title}' has been viewed"
            url_for_freelancer = f"/proposal-view-page/{instance.id}/"
            Notification.objects.create(user=instance.freelancer, message=message, url=url_for_freelancer)
            # notify_user(instance.freelancer, {'message': message, 'url': url_for_freelancer})

        if 'accepted' in dirty_fields and instance.accepted:
            message = f"Your proposal for job '{instance.job.title}' has been accepted"
            url_for_freelancer = f"/proposal-view-page/{instance.id}/"
            Notification.objects.create(user=instance.freelancer, message=message, url=url_for_freelancer)
            # notify_user(instance.freelancer, {'message': message, 'url': url_for_freelancer})

        if 'declined' in dirty_fields and instance.declined:
            message = f"Your proposal for job '{instance.job.title}' has been declined"
            url_for_freelancer = f"/proposal-view-page/{instance.id}/"
            Notification.objects.create(user=instance.freelancer, message=message, url=url_for_freelancer)
            # notify_user(instance.freelancer, {'message': message, 'url': url_for_freelancer})

@receiver(post_save, sender=Job)
def create_job_notification(sender, instance, created, **kwargs):
    if created:
        message = f"Your job '{instance.title}' has been posted"
        url = f"/job-detail/{instance.id}/"
        Notification.objects.create(user=instance.client, message=message)
        # notify_user(instance.client, message)

@receiver(post_save, sender=HiredFreelancer)
def job_started_notification(sender, instance, created, **kwargs):
    if created and instance.started:
        message_for_client = f"The job '{instance.job.title}' has started."
        Notification.objects.create(user=instance.job.client, message=message_for_client)
        # notify_user(instance.job.client, message_for_client)

        message_for_freelancer = f"You have started working on the job '{instance.job.title}'."
        Notification.objects.create(user=instance.freelancer, message=message_for_freelancer)
        # notify_user(instance.freelancer, message_for_freelancer)

@receiver(post_save, sender=JobSubmission)
def job_submission_notification(sender, instance, created, **kwargs):
    if created:
        message_for_client = f"A submission has been made for the job '{instance.job.title}'."
        Notification.objects.create(user=instance.job.client, message=message_for_client)
        # notify_user(instance.job.client, message_for_client)

@receiver(post_save, sender=Revision)
def job_revision_notification(sender, instance, created, **kwargs):
    if created:
        message_for_client = f"A revision has been submitted for the job '{instance.job.title}'."
        Notification.objects.create(user=instance.job.client, message=message_for_client)
        # notify_user(instance.job.client, message_for_client)

        message_for_freelancer = f"You have submitted a revision for the job '{instance.job.title}'."
        Notification.objects.create(user=instance.freelancer, message=message_for_freelancer)
        # notify_user(instance.freelancer, message_for_freelancer)

@receiver(post_save, sender=HiredFreelancer)
def job_completed_notification(sender, instance, created, **kwargs):
    if created and instance.completed:
        message_for_client = f"The job '{instance.job.title}' has been completed."
        Notification.objects.create(user=instance.job.client, message=message_for_client)
        # notify_user(instance.job.client, message_for_client)

        message_for_freelancer = f"The job '{instance.job.title}' has been completed."
        Notification.objects.create(user=instance.freelancer, message=message_for_freelancer)
        # notify_user(instance.freelancer, message_for_freelancer)

@receiver(post_save, sender=HiredFreelancer)
def revision_request_notification(sender, instance, created, **kwargs):
    if created and instance.job.revisions:
        message_for_freelancer = f"A revision has been requested for the job '{instance.job.title}'."
        Notification.objects.create(user=instance.freelancer, message=message_for_freelancer)
        # notify_user(instance.freelancer, message_for_freelancer)
 
@receiver(post_save, sender=Invite)
def create_invite_notification(sender, instance, created, **kwargs):
    freelancer_name = instance.freelancer.username
    client_name = instance.client.username
    job_title = instance.job.title

    if created:
        # Notification for the client
        message_for_client = f"Your invite for the job '{job_title}' has been sent to {freelancer_name}."
        url_for_client = f"/job-detail/{instance.job.id}/"
        Notification.objects.create(user=instance.client, message=message_for_client, url=url_for_client)
        # notify_user(instance.client, {'message': message_for_client, 'url': url_for_client})

        # Notification for the freelancer
        message_for_freelancer = f"You have received an invite from {client_name} for the job '{job_title}'."
        url_for_freelancer = f"/detail/{instance.job.id}/"
        Notification.objects.create(user=instance.freelancer, message=message_for_freelancer, url=url_for_freelancer)
        # notify_user(instance.freelancer, {'message': message_for_freelancer, 'url': url_for_freelancer})

    elif instance.accepted:
        # Notification for the client
        message_for_client = f"The invite for the job '{job_title}' has been accepted by {freelancer_name}."
        url_for_client = f"/job-detail/{instance.job.id}/"
        Notification.objects.create(user=instance.client, message=message_for_client, url=url_for_client)
        # notify_user(instance.client, {'message': message_for_client, 'url': url_for_client})

        # Notification for the freelancer
        message_for_freelancer = f"You have accepted the invite for the job '{job_title}'."
        url_for_freelancer = f"/detail/{instance.job.id}/"
        Notification.objects.create(user=instance.freelancer, message=message_for_freelancer, url=url_for_freelancer)
        # notify_user(instance.freelancer, {'message': message_for_freelancer, 'url': url_for_freelancer})

    elif instance.declined:
        # Notification for the client
        message_for_client = f"The invite for the job '{job_title}' has been declined by {freelancer_name}."
        url_for_client = f"/job-detail/{instance.job.id}/"
        Notification.objects.create(user=instance.client, message=message_for_client, url=url_for_client)
        # notify_user(instance.client, {'message': message_for_client, 'url': url_for_client})

        # Notification for the freelancer
        message_for_freelancer = f"You have declined the invite for the job '{job_title}'."
        url_for_freelancer = f"/detail/{instance.job.id}/"
        Notification.objects.create(user=instance.freelancer, message=message_for_freelancer, url=url_for_freelancer)
        # notify_user(instance.freelancer, {'message': message_for_freelancer, 'url': url_for_freelancer})