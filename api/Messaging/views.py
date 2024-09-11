from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.models import Messaging, UploadFile, CustomUser
from .serializers import MessageSerializer 
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from collections import defaultdict
from django.db.models import Subquery, OuterRef
from django.db.models import Q
from django.db.models import Case, Count, When, F
from django.contrib.auth import get_user_model

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def send_message(request):
    receiver_id = request.data.get('receiver')
    sender = request.user

    try:
        receiver = sender.__class__.objects.get(id=receiver_id)
    except sender.__class__.DoesNotExist:
        return Response({'error': f'{sender.__class__.__name__} does not exist'}, status=404)

    serializer = MessageSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        message = serializer.save(sender=sender, receiver=receiver)

        # Handle file attachments
        files = request.FILES.getlist('files')
        for file_data in files:
            upload_file = UploadFile.objects.create(file=file_data)
            message.files.add(upload_file)

        # Send message over WebSocket
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{sender.id}",
            {
                "type": "chat.message",
                "message": serializer.data
            }
        )

        return Response(serializer.data, status=201)
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_status(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        status = 'online' if user.is_online else 'offline'
        return Response({'status': status}, status=200)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_message_list(request): 
    user = request.user

    # Retrieve the latest message for each unique combination of sender and recipient
    latest_message_ids = Messaging.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).values('sender', 'receiver').annotate(
        last_msg=Subquery(
            Messaging.objects.filter(
                Q(sender=OuterRef('sender'), receiver=user) |
                Q(receiver=OuterRef('sender'), sender=user)
            ).order_by('-id')[:1].values('id')
        )
    ).values_list('last_msg', flat=True)

    # Retrieve the full message objects based on the latest message IDs
    latest_messages = Messaging.objects.filter(id__in=latest_message_ids).order_by('-timestamp')

    # Count the unread messages for each conversation
    latest_messages = latest_messages.annotate(
        unread_count=Count(
            Case(
                When(sender=user, is_read=False, receiver=F('receiver'), then=1),
                When(receiver=user, is_read=False, sender=F('sender'), then=1),
            )
        )
    )

    # Serialize the messages
    serializer = MessageSerializer(latest_messages, many=True, context={'request': request})
    response_data = serializer.data
    
    # Include partner id in each message
    for data in response_data:
        data['partner_id'] = data['receiver'] if data['sender'] == user.id else data['sender']

    return Response(response_data)

 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_messages_with_user(request, user_id):
    sender = request.user

    try:
        receiver = sender.__class__.objects.get(id=user_id)
    except sender.__class__.DoesNotExist:
        return Response({'error': f'{sender.__class__.__name__} does not exist'}, status=404)

    # Define a function to get the queryset
    def get_queryset(sender_id, receiver_id):
        messages = Messaging.objects.filter(sender__in=[sender_id, receiver_id], receiver__in=[sender_id, receiver_id])
        return messages

    # Get the queryset using the function
    queryset = get_queryset(sender.id, user_id)

    # Mark the messages as read
    queryset.filter(receiver=sender, is_read=False).update(is_read=True)

    # Serialize the queryset and return the response
    serializer = MessageSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_unread_messages_count(request):
    user = request.user
    unread_count = Messaging.objects.filter(receiver=user, is_read=False).count()
    return Response({'unread_count': unread_count})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_staff_status(request):
    User = get_user_model()
    staff_members = User.objects.filter(is_staff=True)

    staff_statuses = []
    for staff in staff_members:
        staff_statuses.append({
            'id': staff.id,
            'is_online': staff.is_online,
        })

    return Response(staff_statuses, status=200)