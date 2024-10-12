# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models import Proposal, Job, HiredFreelancer, JobSubmission, Revision, Invite
from .firebase_utils import send_fcm_notification
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Proposal)
def create_proposal_notification(sender, instance, created, **kwargs):
    if created:
        # Retrieve FCM tokens for client and freelancer
        client_token = instance.job.client.fcm_token
        freelancer_token = instance.freelancer.fcm_token

        message_for_client = f"Your job '{instance.job.title}' has received a new proposal from {instance.freelancer.username}."
        send_fcm_notification(
            fcm_token=client_token,
            title="New Proposal Received",
            body=message_for_client,
            data={"url": f"/job-detail/{instance.job.id}/"}
        )

        message_for_freelancer = f"New proposal submitted for job: {instance.job.title}"
        send_fcm_notification(
            fcm_token=freelancer_token,
            title="Proposal Submitted",
            body=message_for_freelancer,
            data={"url": f"/proposal-view-page/{instance.id}/"}
        )

@receiver(post_save, sender=Job)
def create_job_notification(sender, instance, created, **kwargs):
    if created:
        client_token = instance.client.fcm_token
        message = f"Your job '{instance.title}' has been posted."
        send_fcm_notification(
            fcm_token=client_token,
            title="Job Posted",
            body=message,
            data={"url": f"/job-detail/{instance.id}/"}
        )

@receiver(post_save, sender=HiredFreelancer)
def job_started_notification(sender, instance, created, **kwargs):
    if created and instance.started:
        client_token = instance.job.client.fcm_token
        freelancer_token = instance.freelancer.fcm_token

        message_for_client = f"The job '{instance.job.title}' has started."
        send_fcm_notification(
            fcm_token=client_token,
            title="Job Started",
            body=message_for_client
        )

        message_for_freelancer = f"You have started working on the job '{instance.job.title}'."
        send_fcm_notification(
            fcm_token=freelancer_token,
            title="Job Started",
            body=message_for_freelancer
        )

@receiver(post_save, sender=JobSubmission)
def job_submission_notification(sender, instance, created, **kwargs):
    if created:
        client_token = instance.job.client.fcm_token
        message_for_client = f"A submission has been made for the job '{instance.job.title}'."
        send_fcm_notification(
            fcm_token=client_token,
            title="Job Submission",
            body=message_for_client
        )

@receiver(post_save, sender=Revision)
def job_revision_notification(sender, instance, created, **kwargs):
    if created:
        client_token = instance.job.client.fcm_token
        freelancer_token = instance.freelancer.fcm_token

        message_for_client = f"A revision has been submitted for the job '{instance.job.title}'."
        send_fcm_notification(
            fcm_token=client_token,
            title="Revision Submitted",
            body=message_for_client
        )

        message_for_freelancer = f"You have submitted a revision for the job '{instance.job.title}'."
        send_fcm_notification(
            fcm_token=freelancer_token,
            title="Revision Submitted",
            body=message_for_freelancer
        )

@receiver(post_save, sender=HiredFreelancer)
def job_completed_notification(sender, instance, created, **kwargs):
    if created and instance.completed:
        client_token = instance.job.client.fcm_token
        freelancer_token = instance.freelancer.fcm_token

        message_for_client = f"The job '{instance.job.title}' has been completed."
        send_fcm_notification(
            fcm_token=client_token,
            title="Job Completed",
            body=message_for_client
        )

        message_for_freelancer = f"The job '{instance.job.title}' has been completed."
        send_fcm_notification(
            fcm_token=freelancer_token,
            title="Job Completed",
            body=message_for_freelancer
        )

@receiver(post_save, sender=Invite)
def create_invite_notification(sender, instance, created, **kwargs):
    freelancer_token = instance.freelancer.fcm_token
    client_token = instance.client.fcm_token
    job_title = instance.job.title

    if created:
        message_for_client = f"Your invite for the job '{job_title}' has been sent to {instance.freelancer.username}."
        send_fcm_notification(
            fcm_token=client_token,
            title="Invite Sent",
            body=message_for_client
        )

        message_for_freelancer = f"You have received an invite from {instance.client.username} for the job '{job_title}'."
        send_fcm_notification(
            fcm_token=freelancer_token,
            title="Job Invite",
            body=message_for_freelancer
        )

    elif instance.accepted:
        message_for_client = f"The invite for the job '{job_title}' has been accepted by {instance.freelancer.username}."
        send_fcm_notification(
            fcm_token=client_token,
            title="Invite Accepted",
            body=message_for_client
        )

        message_for_freelancer = f"You have accepted the invite for the job '{job_title}'."
        send_fcm_notification(
            fcm_token=freelancer_token,
            title="Invite Accepted",
            body=message_for_freelancer
        )

    elif instance.declined:
        message_for_client = f"The invite for the job '{job_title}' has been declined by {instance.freelancer.username}."
        send_fcm_notification(
            fcm_token=client_token,
            title="Invite Declined",
            body=message_for_client
        )

        message_for_freelancer = f"You have declined the invite for the job '{job_title}'."
        send_fcm_notification(
            fcm_token=freelancer_token,
            title="Invite Declined",
            body=message_for_freelancer
        )
