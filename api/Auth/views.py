from django.contrib.auth.hashers import check_password, is_password_usable
from rest_framework.decorators import api_view, authentication_classes, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from api.models import Client, Freelancer, Wallet, CustomUser, Subject, Style, AssignmentType, Language, ServiceType, Level, EducationlLevel, Test, LineSpacing
from .serializers import (ClientSerializer, LanguageSerializer,
                           FreelancerSerializer , SubjectSerializer,
                           ClientProfileSerializer, StyleSerializer,
                           FreelancerProfileSerializer, AssignmentTypeSerializer,
                           LogoutSerializer, ServiceTypeSerializer,
                             UserStatusSerializer, SupportSerializer, LevelSerializer,
                               EducationLevelSerializer, TestSerializer, ChangePasswordSerializer, ResetPasswordSerializer, LineSpacingSerializer)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
import bcrypt 
import random
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from .ai_utils import generate_topic
from django.shortcuts import redirect
from django.contrib.auth import login
from social_django.utils import psa
from django.contrib.auth import login as auth_login
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.utils import timezone
from django.contrib.auth.tokens import default_token_generator
import datetime
            

@api_view(['POST'])
@permission_classes([])
def request_password_reset(request):
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(work_email=email)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User with this email does not exist'}, status=status.HTTP_404_NOT_FOUND)

    # Generate token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))

    # Create password reset URL
    reset_url = f"{settings.RESET_PASSWORD_URL}{uid}/{token}/"

    # Send email
    subject = 'Password Reset Request'
    html_message = render_to_string('password_reset_email.html', {'reset_url': reset_url, 'user': user})
    plain_message = strip_tags(html_message)
    from_email = 'no-reply@yourdomain.com'
    recipient_list = [user.work_email] 

    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

    return Response({'message': 'Password reset email sent'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([])
def reset_password(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        serializer = ResetPasswordSerializer(data=request.data, instance=user)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password reset successful'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({'error': 'Invalid token or user'}, status=status.HTTP_400_BAD_REQUEST)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_subjects(request):
    subjects = Subject.objects.all()
    serializer = SubjectSerializer(subjects, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_service_types(request):
    service_type = ServiceType.objects.all()
    serializer = ServiceTypeSerializer(service_type, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_line_spacing(request):
    line_spacing = LineSpacing.objects.all()
    serializer = LineSpacingSerializer(line_spacing, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_levels(request):
    levels = Level.objects.all()
    serializer = LevelSerializer(levels, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_educations(request):
    education = EducationlLevel.objects.all()
    serializer = EducationLevelSerializer(education, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_languages(request):
    languages = Language.objects.all()
    serializer = LanguageSerializer(languages, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_assignment_type(request):
    assignment_type = AssignmentType.objects.all()
    serializer = AssignmentTypeSerializer(assignment_type, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_styles(request):
    style = Style.objects.all()
    serializer = StyleSerializer(style, many=True)
    return Response(serializer.data)


User = get_user_model()

# Function to generate OTP
def generate_otp():
    return str(random.randint(100000, 999999))

# Function to send OTP via email


def send_otp_email(email, otp):
    subject = 'OTP Verification'
    html_message = render_to_string('otp_verification_email.html', {'otp': otp})
    plain_message = strip_tags(html_message)
    from_email = 'no-reply@yourdomain.com'  # Use a no-reply email address
    recipient_list = [email]

    # Send email
    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

def send_interview_preparation_email(email):
    subject = 'Your CV is Under Review'
    html_message = render_to_string('interview_preparation_email.html')
    plain_message = strip_tags(html_message)
    from_email = 'no-reply@yourdomain.com'
    recipient_list = [email]

    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)


@api_view(["OPTIONS", "POST"])
@authentication_classes([])
@permission_classes([])
@parser_classes([MultiPartParser, FormParser])
def create_support(request):
    if request.method == 'POST':
        serializer = SupportSerializer(data=request.data)
        if serializer.is_valid():
            support = serializer.save()
            password = request.data.get('password')
            support.set_password(password)  # Use set_password for hashing
            otp = generate_otp()
            support.otp_code = otp
            support.stuff_application = True
            support.save()
            send_otp_email(email=support.work_email, otp=otp)

            # Send interview preparation email
            send_interview_preparation_email(email=support.work_email)

            refresh = RefreshToken.for_user(support)
            token = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            response_data = {
                'message': 'Registration successful. Please check your email for OTP. We are reviewing your CV and will prepare a Zoom call for an interview.',
                'token': token,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        error_response = {field: error[0] for field, error in serializer.errors.items()}
        return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_200_OK)



@api_view(["OPTIONS", "POST"])
@authentication_classes([])
@permission_classes([])
def create_client(request):
    if request.method == 'POST':
        serializer = ClientSerializer(data=request.data)
        if serializer.is_valid():
            client = serializer.save()
            password = request.data.get('password')
            client.set_password(password)  # Use set_password for hashing
            otp = generate_otp()
            client.otp_code = otp
            client.client_status = True
            client.verified = True
            client.save()
            send_otp_email(email=client.work_email, otp=otp)
            refresh = RefreshToken.for_user(client)
            token = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            response_data = {
                'message': 'Registration successful. Please check your email for OTP.',
                'token': token,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        error_response = {field: error[0] for field, error in serializer.errors.items()}
        return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_200_OK)

@api_view(["OPTIONS", "POST"])
@authentication_classes([])
@permission_classes([])
def create_freelancer(request):
    if request.method == 'POST':
        serializer = FreelancerSerializer(data=request.data)
        if serializer.is_valid():
            freelancer = serializer.save()
            password = request.data.get('password')
            freelancer.set_password(password)  # Use set_password for hashing
            otp = generate_otp()
            freelancer.otp_code = otp
            freelancer.freelancer_status = True
            freelancer.save()
            send_otp_email(email=freelancer.work_email, otp=otp)
            refresh = RefreshToken.for_user(freelancer)
            token = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            response_data = {
                'message': 'Registration successful. Please check your email for OTP.',
                'token': token,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        error_response = {field: error[0] for field, error in serializer.errors.items()}
        return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def verify_otp(request):
    if request.method == 'POST':
        otp = request.data.get('otp')

        if not otp:
            return Response({'error': 'otp is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_instance = get_object_or_404(CustomUser, otp_code=otp)

        user_instance.email_verified = True
        user_instance.save()

        Wallet.objects.create(user=request.user, balance=0)

        # Check if the user is a freelancer
        freelancer_status = hasattr(user_instance, 'freelancer')
        client_status = hasattr(user_instance, 'client')

        response_data = {
            'message': 'Otp Verified. your email is now verified',
            'freelancer_status': freelancer_status,
            'client_status': client_status,
            'is_staff': user_instance.is_staff,
            'stuff_application': user_instance.stuff_application,
        }
        return Response(response_data, status=status.HTTP_200_OK)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_test_topic(request):
    freelancer = Freelancer.objects.get(id=request.user.id)
    skills = freelancer.skills.all()
    subjects = freelancer.subject.all()
 
    if not skills or not subjects:
        return Response({'error': 'Freelancer must have at least one skill and one subject.'}, status=status.HTTP_400_BAD_REQUEST)

    skill = random.choice(skills).name
    subject = random.choice(subjects).name
    topic = generate_topic(skill, subject)

    return Response({'topic': topic}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_test(request):
    try:
        freelancer = request.user.freelancer  # Get the freelancer from the authenticated user
    except Freelancer.DoesNotExist:
        return Response({'error': 'Freelancer not found.'}, status=status.HTTP_404_NOT_FOUND)

    data = request.data.copy()
    data['freelancer'] = freelancer  # Assign freelancer's ID to the freelancer field

    serializer = TestSerializer(data=data)
    if serializer.is_valid():
        serializer.save(freelancer=freelancer)  # Save the Test instance with the freelancer
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def login(request):
    if request.method == 'POST':
        work_email = request.data.get('work_email')
        password = request.data.get('password')
        if not work_email or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(CustomUser, work_email=work_email)
        if not user.is_active:
            return Response({'error': 'Account is inactive.'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.email_verified:
            return Response({'error': 'Email is not verified.'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.verified:
            return Response({'error': 'Credentials not verified.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.suspend:
            return Response({'error': 'Account is suspended.'}, status=status.HTTP_401_UNAUTHORIZED)
        user = authenticate(username=user.username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            token = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            freelancer_status = hasattr(user, 'freelancer')
            client_status = hasattr(user, 'client')
            response_data = {
                'message': 'Login successful.',
                'token': token,
                'freelancer_status': freelancer_status,
                'client_status': client_status,
                'is_staff': user.is_staff,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        serializer.save()
        
        subject = 'Your Password Has Been Changed'
        html_message = render_to_string('password_change_notification_email.html', {'user': user})
        plain_message = strip_tags(html_message)
        from_email = 'no-reply@yourdomain.com'
        recipient_list = [user.work_email]
        
        # Send email
        send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)
        
        return Response({'message': 'Password updated successfully and notification email sent.'}, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user(request):
    user = CustomUser.objects.get(id=request.user.id)
    serializer = UserStatusSerializer(user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def client_info(request):
    client = Client.objects.get(id=request.user.id)
    serializer = ClientProfileSerializer(client)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def freelancer_info(request):
    freelancer_instance = Freelancer.objects.get(id=request.user.id)
    serializer = FreelancerProfileSerializer(freelancer_instance)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def change_email(request):
    user = request.user
    new_email = request.data.get('new_email')

    if not new_email:
        return Response({'error': 'New email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the new email is different from the current email
    if user.work_email == new_email:
        return Response({'error': 'New email should be different from the current email.'}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the new email already exists in the system
    if User.objects.filter(work_email=new_email).exists():
        return Response({'error': 'Email address already exists.'}, status=status.HTTP_400_BAD_REQUEST)

    # Update the user's work_email and set email_verified to False
    user.work_email = new_email
    user.email_verified = False
    user.save()

    # Generate and save OTP for the new email
    otp = generate_otp()
    user.otp_code = otp
    user.save()

    # Send OTP via email to the new email
    send_otp_email(email=new_email, otp=otp)

    response_data = {
        'message': 'Email change request successful. Please check your new email for OTP.',
    }
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    serializer_class = LogoutSerializer
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(status=status.HTTP_204_NO_CONTENT)
    

@api_view(['GET'])
@permission_classes([])
def google_login(request):
    return redirect('/auth/login/google-oauth2/')

@api_view(['GET'])
@permission_classes([])
@psa('social:complete')
def google_complete(request, backend):
    user = request.backend.do_auth(request.GET.get('code'))
    if user:
        auth_login(request, user)
        return Response({'detail': 'Google login successful'}, status=status.HTTP_200_OK)
    else:
        return Response({'detail': 'Google login failed'}, status=status.HTTP_400_BAD_REQUEST)

import logging
import traceback
import requests
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
# from allauth.socialaccount.providers.linkedin.views import LinkedInOAuth2Adapter
from allauth.socialaccount.providers.microsoft.views import MicrosoftGraphOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.helpers import complete_social_login
from allauth.socialaccount.models import SocialApp, SocialToken, SocialLogin
from allauth.core.exceptions import ImmediateHttpResponse
from django.conf import settings
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from api.models import CustomUser, Client, Freelancer

logger = logging.getLogger(__name__)

@api_view(['POST'])
@authentication_classes([])
@permission_classes([])
def signup_with_social(request):
    token = request.data.get('access_token')
    role = request.data.get('role')
    provider = request.data.get('provider')

    if not token:
        logger.error("Access token is missing")
        return Response({'error': 'Access token is required'}, status=status.HTTP_400_BAD_REQUEST)

    if not role or role not in ['client', 'freelancer']:
        logger.error("Invalid role or role is missing")
        return Response({'error': 'Role is required and must be either "client" or "freelancer"'}, status=status.HTTP_400_BAD_REQUEST)

    if not provider or provider not in ['google', 'linkedin', 'microsoft']:
        logger.error("Invalid provider or provider is missing")
        return Response({'error': 'Provider is required and must be either "google", "linkedin", or "microsoft"'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        logger.info(f"Authenticating user with token: {token} for provider: {provider}")

        # Choose the correct adapter based on the provider
        if provider == 'google':
            adapter = GoogleOAuth2Adapter(request)
            token_info_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        # elif provider == 'linkedin':
        #     adapter = LinkedInOAuth2Adapter(request)
        #     token_info_url = "https://api.linkedin.com/v2/me"
        elif provider == 'microsoft':
            adapter = MicrosoftGraphOAuth2Adapter(request)
            token_info_url = "https://graph.microsoft.com/v1.0/me"

        # Retrieve the SocialApp instance for the provider
        app = SocialApp.objects.get(provider=adapter.provider_id, sites__id=settings.SITE_ID)

        # Make a request to the provider's endpoint to fetch user info
        response = requests.get(token_info_url, params={'access_token': token})
        response.raise_for_status()  # Raise an error for bad status codes
        token_info = response.json()

        # Create SocialToken and SocialLogin
        social_token = SocialToken(token=token)
        login = adapter.complete_login(request, app, token_info)
        login.token = social_token
        login.state = SocialLogin.state_from_request(request)
        complete_social_login(request, login)

        user = login.account.user
        logger.info(f"User authenticated: {user}")

        if user and user.is_active:
            logger.info(f"User is active: {user}")

            # Check if email already exists
            if CustomUser.objects.filter(work_email=user.email).exists():
                logger.info(f"User with email {user.email} already exists.")
                custom_user = CustomUser.objects.get(work_email=user.email)
            else:
                # Check if username already exists
                username_exists = CustomUser.objects.filter(username=user.username).exists()
                logger.info(f"Username {user.username} exists: {username_exists}")

                # Create a unique username if the existing username is taken
                original_username = user.username
                counter = 1
                while username_exists:
                    user.username = f"{original_username}_{counter}"
                    username_exists = CustomUser.objects.filter(username=user.username).exists()
                    counter += 1

                logger.info(f"Creating new user with username {user.username} and email {user.email}")
                extra_data = SocialAccount.objects.filter(user=user, provider=adapter.provider_id).first().extra_data
                profile_image_url = extra_data.get('picture')

                custom_user = CustomUser.objects.create(
                    username=user.username,
                    work_email=user.email,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    is_active=True,
                    email_verified=True,
                    profile_image=profile_image_url,
                )
                custom_user.save()

                if role == 'client':
                    Client.objects.create(user=custom_user, client_status=True)
                elif role == 'freelancer':
                    Freelancer.objects.create(user=custom_user, freelancer_status=True)

            refresh = RefreshToken.for_user(custom_user)
            token = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }

            response_data = {
                'message': 'Signup successful.',
                'token': token,
                'username': custom_user.username,
                'email': custom_user.work_email,
                'profile_image': custom_user.profile_image.url if custom_user.profile_image else None,
            }

            return Response(response_data, status=status.HTTP_200_OK)
        else:
            logger.error(f"Authentication failed for user: {user}")
            return Response({'error': 'Authentication failed'}, status=status.HTTP_401_UNAUTHORIZED)

    except SocialApp.DoesNotExist:
        logger.error("SocialApp not configured correctly")
        return Response({'error': 'Social authentication is not configured correctly.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except ImmediateHttpResponse as e:
        return e.response
    except Exception as e:
        logger.error(f"Signup with social provider failed: {str(e)}")
        logger.error(traceback.format_exc())
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

