from django.shortcuts import get_object_or_404 # type: ignore
from rest_framework.response import Response # type: ignore 
from rest_framework.parsers import MultiPartParser, FormParser # type: ignore 
from rest_framework import status # type: ignore
from rest_framework.decorators import api_view, permission_classes, parser_classes # type: ignore
from rest_framework.permissions import IsAuthenticated # type: ignore
from api.models import Job, Notification, CustomUser, Proposal
from .serializers import NotificationSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is logged in
@parser_classes([MultiPartParser, FormParser])  # Handle multipart form data
def create_proposal_viewed_notification(request):
    # Get required fields from the request data
    freelancer_message = request.data.get('freelancer_message')
    freelancer_icon = request.data.get('freelancer_icon')
    freelancer_url = request.data.get('freelancer_url')
    proposal_id = request.data.get('proposal_id')

    # Fetch the proposal by ID
    proposal = get_object_or_404(Proposal, id=proposal_id)

    # Get the freelancer associated with the proposal
    freelancer = proposal.freelancer

    # Create a notification for the freelancer
    freelancer_notification = Notification.objects.create(
        user=freelancer,  # Send the notification to the freelancer
        message=freelancer_message,
        icon=freelancer_icon,
        url=freelancer_url
    )

    # Serialize and return the freelancer notification
    freelancer_serializer = NotificationSerializer(freelancer_notification)

    return Response({
        'freelancer_notification': freelancer_serializer.data
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is logged in
@parser_classes([MultiPartParser, FormParser])
def create_notification(request):
    client_id = request.data.get('client_id')
    job_id = request.data.get('job_id')
    freelancer_message = request.data.get('freelancer_message')
    client_message = request.data.get('client_message')
    freelancer_icon = request.data.get('freelancer_icon')
    client_icon = request.data.get('client_icon')
    freelancer_url = request.data.get('freelancer_url')
    client_url = request.data.get('client_url')

    # Use the authenticated user as the freelancer
    freelancer = request.user
    job = get_object_or_404(Job, id=job_id)
    client = get_object_or_404(CustomUser, id=client_id)  # Get client from request

    # Create a notification for the freelancer
    freelancer_notification = Notification.objects.create(
        user=freelancer,
        message=freelancer_message,
        icon=freelancer_icon,
        url=freelancer_url
    )

    # Create a notification for the client
    client_notification = Notification.objects.create(
        user=client,
        message=client_message,
        icon=client_icon,
        url=client_url
    )

    # Serialize and return the notifications
    freelancer_serializer = NotificationSerializer(freelancer_notification)
    client_serializer = NotificationSerializer(client_notification)

    return Response({
        'freelancer_notification': freelancer_serializer.data,
        'client_notification': client_serializer.data
    }, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is logged in
@parser_classes([MultiPartParser, FormParser])
def create_notification_client_signle(request):
    # Extract the client message and other relevant fields from the request
    client_message = request.data.get('client_message')
    client_icon = request.data.get('client_icon')
    client_url = request.data.get('client_url')

    # Use the authenticated user as the client
    client = request.user

    # Create a notification for the client
    client_notification = Notification.objects.create(
        user=client,
        message=client_message,
        icon=client_icon,
        url=client_url
    )

    # Serialize and return the client notification
    client_serializer = NotificationSerializer(client_notification)

    return Response({
        'client_notification': client_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is logged in
@parser_classes([MultiPartParser, FormParser])
def create_notification_client(request):
    freelancer_id = request.data.get('freelancer_id')  # Get freelancer_id from the request
    # job_id = request.data.get('job_id')
    freelancer_message = request.data.get('freelancer_message')
    client_message = request.data.get('client_message')
    freelancer_icon = request.data.get('freelancer_icon')
    client_icon = request.data.get('client_icon')
    freelancer_url = request.data.get('freelancer_url')
    client_url = request.data.get('client_url')

    # Use the authenticated user as the client
    client = request.user
    # job = get_object_or_404(Job, id=job_id)
    
    # Get the freelancer from the provided freelancer_id
    freelancer = get_object_or_404(CustomUser, id=freelancer_id)

    # Create a notification for the freelancer
    freelancer_notification = Notification.objects.create(
        user=freelancer,
        message=freelancer_message,
        icon=freelancer_icon,
        url=freelancer_url
    )

    # Create a notification for the client
    client_notification = Notification.objects.create(
        user=client,
        message=client_message,
        icon=client_icon,
        url=client_url
    )

    # Serialize and return the notifications
    freelancer_serializer = NotificationSerializer(freelancer_notification)
    client_serializer = NotificationSerializer(client_notification)

    return Response({
        'freelancer_notification': freelancer_serializer.data,
        'client_notification': client_serializer.data
    }, status=status.HTTP_201_CREATED)



@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Ensure the user is logged in
def get_user_notifications(request):
    user = request.user  # Get the currently logged-in user
    notifications = Notification.objects.filter(user=user).order_by('-timestamp')  # Use timestamp instead of created_at
    serializer = NotificationSerializer(notifications, many=True)  # Serialize the notifications
    
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is logged in
def mark_notification_as_read(request, notification_id):
    user = request.user  # Get the logged-in user
    notification = get_object_or_404(Notification, id=notification_id, user=user)  # Ensure notification belongs to the user

    # Mark the notification as read
    notification.is_read = True
    notification.save()

    # Serialize and return the updated notification
    serializer = NotificationSerializer(notification)
    return Response(serializer.data, status=status.HTTP_200_OK)

# 2. Mark all notifications as read
@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is logged in
def mark_all_notifications_as_read(request):
    user = request.user  # Get the logged-in user
    notifications = Notification.objects.filter(user=user, is_read=False)  # Get all unread notifications

    # Mark all notifications as read
    notifications.update(is_read=True)

    return Response({'message': 'All notifications marked as read.'}, status=status.HTTP_200_OK)

# 3. Delete a single notification
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  # Ensure the user is logged in
def delete_notification(request, notification_id):
    user = request.user  # Get the logged-in user
    notification = get_object_or_404(Notification, id=notification_id, user=user)  # Ensure notification belongs to the user

    # Delete the notification
    notification.delete()

    return Response({'message': 'Notification deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

# 4. Delete all notifications
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  # Ensure the user is logged in
def delete_all_notifications(request):
    user = request.user  # Get the logged-in user
    notifications = Notification.objects.filter(user=user)  # Get all notifications for the user

    # Delete all notifications
    notifications.delete()

    return Response({'message': 'All notifications deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
