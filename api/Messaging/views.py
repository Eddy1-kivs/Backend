from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from api.models import Messaging, CustomUser
from .serializers import MessageSerializer, CustomUserSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from collections import defaultdict
from django.db.models import Subquery, OuterRef
from django.db.models import Case, Count, When, F
from django.contrib.auth import get_user_model

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def send_message(request):
    receiver_id = request.data.get('receiver') 
    sender = request.user

    # Get the receiver user by ID
    try:
        receiver = CustomUser.objects.get(id=receiver_id)
    except CustomUser.DoesNotExist:
        return Response({'error': f'User with ID {receiver_id} does not exist'}, status=404)

    # Validate the message data using the serializer
    serializer = MessageSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        # Save the message with the sender and receiver
        message = serializer.save(sender=sender, receiver=receiver)

        # Handle file attachments if provided
        files = request.FILES.getlist('files')
        for file_data in files:
            upload_file = UploadFile.objects.create(file=file_data)
            message.files.add(upload_file)

        return Response(serializer.data, status=201)
    
    # Return errors if the serializer is invalid
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

    # Retrieve the latest message for each unique combination of sender and receiver
    latest_message_ids = Messaging.objects.filter(
        Q(sender=user) | Q(receiver=user)
    ).values('sender', 'receiver').annotate(
        last_msg=Subquery(
            Messaging.objects.filter(
                Q(sender=OuterRef('sender'), receiver=OuterRef('receiver')) |
                Q(sender=OuterRef('receiver'), receiver=OuterRef('sender'))
            ).order_by('-id')[:1].values('id')
        )
    ).values_list('last_msg', flat=True)

    # Retrieve the full message objects based on the latest message IDs
    latest_messages = Messaging.objects.filter(id__in=latest_message_ids).order_by('-timestamp')

    # Serialize the messages
    serializer = MessageSerializer(latest_messages, many=True, context={'request': request})
    response_data = serializer.data

    # Calculate unread message count manually
    for data in response_data:
        if data['sender'] == user.id:
            unread_count = Messaging.objects.filter(sender=data['receiver'], receiver=user, is_read=False).count()
        else:
            unread_count = Messaging.objects.filter(sender=user, receiver=data['sender'], is_read=False).count()

        data['unread_count'] = unread_count

        # Include partner information (the other user in the conversation)
        data['partner_id'] = data['receiver'] if data['sender'] == user.id else data['sender']
        data['partner_username'] = data['receiver_username'] if data['sender'] == user.id else data['sender_username']
        data['partner_profile_image'] = data['receiver_profile_image'] if data['sender'] == user.id else data['sender_profile_image']

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_messages_or_users(request): 
    user = request.user
    search_query = request.query_params.get('q', '')

    if not search_query:
        return Response({"error": "No search query provided"}, status=400)

    # Search for messages containing the query (only conversations with the user)
    messages = Messaging.objects.filter(
        Q(sender=user) | Q(receiver=user),
        Q(message__icontains=search_query)  # Search in message content
    ).distinct()

    # Serialize messages
    message_serializer = MessageSerializer(messages, many=True, context={'request': request})

    # Search for users by username (only users the user has chatted with)
    users = CustomUser.objects.filter(
        Q(id__in=Messaging.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).values('sender').distinct()) |
        Q(id__in=Messaging.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).values('receiver').distinct()),
        Q(username__icontains=search_query)  # Search in username
    ).distinct()

    # Serialize users
    user_serializer = CustomUserSerializer(users, many=True)

    return Response({
        'messages': message_serializer.data,
        'users': user_serializer.data
    }, status=200)