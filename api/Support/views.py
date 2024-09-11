from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from api.models import CustomUser, Freelancer, Suspension, HiredFreelancer, Client
from .serializers import CustomUserSerializer, FreelancerSerializer, SuspensionSerializer, HiredFreelancerSerializer
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
from django.utils import timezone
from rest_framework import status
from datetime import datetime
from django.db.models import Q
from django.template.loader import render_to_string
from django.utils.html import strip_tags

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def clients(request):
    # Filter clients based on client_status
    clients = CustomUser.objects.filter(client_status=True)
    serializer = CustomUserSerializer(clients, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def freelancers(request):
    # Filter freelancers based on freelancer_status
    freelancers = Freelancer.objects.filter(freelancer_status=True)
    serializer = FreelancerSerializer(freelancers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def suspended_users(request):
    # Filter suspended users
    suspended_users = CustomUser.objects.filter(suspend=True)
    serializer = CustomUserSerializer(suspended_users, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_credentials(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        user.verified = True
        user.save()
        
        # Render the email template
        subject = 'Credentials Verification'
        html_message = render_to_string('verify_credentials_email.html', {'user': user})
        plain_message = strip_tags(html_message)
        from_email = 'no-reply@yourdomain.com'
        recipient_list = [user.work_email]
        
        # Send email
        send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

        serializer = CustomUserSerializer(user)
        return Response(serializer.data)
    except CustomUser.DoesNotExist:
        return Response({"message": "User not found"}, status=404)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_credentials(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        decline_reason = request.data.get('reason')

        if not decline_reason:
            return Response({"message": "Reason for declining credentials is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        # Render the email template
        subject = 'Credentials Declined'
        html_message = render_to_string('decline_credentials_email.html', {'user': user, 'reason': decline_reason})
        plain_message = strip_tags(html_message)
        from_email = 'no-reply@yourdomain.com'
        recipient_list = [user.work_email]
        
        # Send email
        send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
        
        user.delete()
        return Response({"message": "User credentials declined and user deleted successfully."}, status=status.HTTP_200_OK)
    except CustomUser.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def suspend_user(request, user_id):
    try:
        user = CustomUser.objects.get(id=user_id)
        suspension_reason = request.data.get('reason')
        suspension_days_str = request.data.get('days')

        if not suspension_reason:
            return Response({"message": "Suspension reason is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not suspension_days_str:
            return Response({"message": "Suspension days are required"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            suspension_days = int(suspension_days_str)
        except ValueError:
            return Response({"message": "Invalid suspension days format"}, status=status.HTTP_400_BAD_REQUEST)
        
        suspension_end_date = timezone.now() + timedelta(days=suspension_days)
        suspension_end_date_formatted = suspension_end_date.strftime("%B %d, %Y")
        
        Suspension.objects.create(
            user=user,
            suspension_reason=suspension_reason,
            suspension_days=suspension_days,
            suspension_end_date=suspension_end_date
        )
        
        user.suspend = True
        user.save()

        # Render the email template
        subject = 'Account Suspension'
        html_message = render_to_string('suspend_user_email.html', {
            'user': user,
            'reason': suspension_reason,
            'suspension_days': suspension_days,
            'suspension_end_date': suspension_end_date_formatted
        })
        plain_message = strip_tags(html_message)
        from_email = 'no-reply@yourdomain.com'
        recipient_list = [user.work_email]
        
        # Send email
        send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

        serializer = CustomUserSerializer(user)
        return Response(serializer.data)
    except CustomUser.DoesNotExist:
        return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def hired_freelancers(request):
    # Get all hired freelancers
    hired_freelancers = HiredFreelancer.objects.all()
    serializer = HiredFreelancerSerializer(hired_freelancers, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def freelancers_search(request):
    search_query = request.data.get('query', '')
    
    if search_query:
        # Filter freelancers based on search query
        freelancers = Freelancer.objects.filter(
            Q(work_email__icontains=search_query) | Q(username__icontains=search_query)
        ).filter(freelancer_status=True)
    else:
        # Filter all active freelancers
        freelancers = Freelancer.objects.filter(freelancer_status=True)

    serializer = FreelancerSerializer(freelancers, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clients_search(request):
    search_query = request.data.get('query', '')
    
    if search_query:
        # Filter clients based on search query
        clients = CustomUser.objects.filter(
            Q(work_email__icontains=search_query) | Q(username__icontains=search_query),
            client_status=True
        )
    else:
        # Filter all active clients
        clients = CustomUser.objects.filter(client_status=True)

    serializer = CustomUserSerializer(clients, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def hired_freelancers_search(request):
    search_query = request.data.get('order_id', '')
    
    if search_query:
        # Filter hired freelancers based on order ID
        hired_freelancers = HiredFreelancer.objects.filter(order_id=search_query)
    else:
        # Return all hired freelancers if no search query is provided
        hired_freelancers = HiredFreelancer.objects.all()

    serializer = HiredFreelancerSerializer(hired_freelancers, many=True)
    return Response(serializer.data)
