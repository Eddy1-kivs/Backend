# firebase_utils.py

from firebase_admin import messaging
import logging

logger = logging.getLogger(__name__)

def send_fcm_notification(fcm_token, title, body, data=None):
    """
    Send a notification using Firebase Cloud Messaging (FCM).
    
    :param fcm_token: FCM registration token for the device
    :param title: Title of the notification
    :param body: Body of the notification
    :param data: Optional dictionary with additional data to send
    """
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=fcm_token,
        data=data or {}
    )

    try:
        response = messaging.send(message)
        logger.info(f"Successfully sent FCM notification: {response}")
        return response
    except Exception as e:
        logger.error(f"Failed to send FCM notification: {e}")
        return None
