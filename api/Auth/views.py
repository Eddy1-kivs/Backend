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
                             UserStatusSerializer, SupportSerializer, LevelSerializer,UserInfoSerializer,
                               EducationLevelSerializer, TestSerializer, ChangePasswordSerializer, ResetPasswordSerializer,
                               LineSpacingSerializer, TypeSerializer)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate
import random
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from .ai_utils import generate_topic
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.hashers import make_password
from firebase_admin import auth as firebase_auth, exceptions as firebase_exceptions
from django.db import transaction

User = get_user_model()

def verify_firebase_token(token):
    try:
        decoded_token = firebase_auth.verify_id_token(token)
        return decoded_token, None
    except firebase_exceptions.FirebaseError as e:
        return None, str(e)

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

@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def check_email(request):
    work_email = request.data.get('work_email')

    if not work_email:
        return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = CustomUser.objects.get(work_email=work_email)
        
        # Check if the provider_state is True
        if user.provider_state:
            provider = user.provider
            return Response({
                'exists': True,
                'message': f'This email is associated with the {provider} provider. Please sign up using that provider.'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'exists': True,
                'message': 'This email is registered but not linked to any provider. You can sign up normally.'
            }, status=status.HTTP_200_OK)

    except CustomUser.DoesNotExist:
        return Response({'exists': False}, status=status.HTTP_200_OK)
    


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
@transaction.atomic
def create_user(request):
    role = request.data.get('role')
    
    # Check for Google OAuth ID in the request data
    if 'google_id' in request.data:
        google_id_token = request.data.get('google_id')
        decoded_token, error = verify_firebase_token(google_id_token)

        if error:
            return Response({'error': f'Google authentication failed: {error}'}, status=status.HTTP_400_BAD_REQUEST)

        google_uid = decoded_token['uid']
        email = decoded_token.get('email')

        if not email:
            return Response({'error': 'Email not found in Firebase token'}, status=status.HTTP_400_BAD_REQUEST)

        # Set up serializer with data for Google OAuth signup
        user_data = request.data.copy()
        user_data['work_email'] = email
        user_data['password'] = make_password('defaultpassword123!')  # Set a default password for OAuth signups

        # Choose serializer based on role
        if role == 'client':
            serializer = ClientSerializer(data=user_data, context={'request': request})  # Add request context here
        elif role == 'freelancer':
            # Check if type (writer or technical) is specified
            freelancer_type = user_data.get('type')
            if freelancer_type not in ['writer', 'technical']:
                return Response({'error': 'Freelancer type must be either writer or technical.'}, status=status.HTTP_400_BAD_REQUEST)

            # Set is_writer or is_technical based on type input
            user_data['is_writer'] = freelancer_type == 'writer'
            user_data['is_technical'] = freelancer_type == 'technical'
            serializer = FreelancerSerializer(data=user_data, context={'request': request})  # Add request context here
        else:
            return Response({'error': 'Invalid role provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate and save the user
        if serializer.is_valid():
            user = serializer.save()
            user.provider = 'google'
            user.provider_uid = google_uid
            user.provider_state = True
            user.email_verified = True
            user.user_status = True

            # Set role-specific status
            if role == 'client':
                user.client_status = True
                user.verified = True
            elif role == 'freelancer':
                user.freelancer_status = True
                Wallet.objects.create(user=user)

            user.save()

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            token = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }

            return Response({
                'message': f'{role.capitalize()} signup successful.',
                'token': token,
                'freelancer_status': user.freelancer_status,
                'client_status': user.client_status,
                'email_verified': user.email_verified,
                'verified': user.verified,
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    else:
        # Regular signup process
        if role == 'client':
            serializer = ClientSerializer(data=request.data, context={'request': request})  # Add request context here
        elif role == 'freelancer':
            freelancer_type = request.data.get('type')
            if freelancer_type not in ['writer', 'technical']:
                return Response({'error': 'Freelancer type must be either writer or technical.'}, status=status.HTTP_400_BAD_REQUEST)

            # Set is_writer or is_technical based on type input
            request.data['is_writer'] = freelancer_type == 'writer'
            request.data['is_technical'] = freelancer_type == 'technical'
            serializer = FreelancerSerializer(data=request.data, context={'request': request})  # Add request context here
        else:
            return Response({'error': 'Invalid role provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate and save the user
        if serializer.is_valid():
            user = serializer.save()
            user.set_password(request.data.get('password'))  # Hash the password
            user.user_status = True

            # Set role-specific status
            if role == 'client':
                user.client_status = True
                user.verified = True
            elif role == 'freelancer':
                user.freelancer_status = True
                Wallet.objects.create(user=user)

            user.otp_code = generate_otp()  # Generate OTP
            user.save()

            # Send OTP email for verification
            send_otp_email(email=user.work_email, otp=user.otp_code)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            token = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }

            return Response({
                'message': f'Registration successful. Check your email for OTP.',
                'token': token,
                'freelancer_status': user.freelancer_status,
                'client_status': user.client_status,
                'email_verified': user.email_verified,
                'verified': user.verified,
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def login(request):
    if 'google_id' in request.data:
        # Google sign-in logic
        google_id_token = request.data.get('google_id')

        if not google_id_token:
            return Response({'error': 'Google ID token is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verify Google ID token
        decoded_token, error = verify_firebase_token(google_id_token)
        if error:
            return Response({'error': f'Google authentication failed: {error}'}, status=status.HTTP_400_BAD_REQUEST)

        google_uid = decoded_token['uid']
        email = decoded_token.get('email')

        if not email:
            return Response({'error': 'Email not found in Firebase token'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if user exists in the database
        user = CustomUser.objects.filter(work_email=email).first()

        if not user:
            return Response({'error': 'User not found. Please sign up first.'}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user signed up with Google
        if user.provider != 'google':  # Only check the 'provider' field
            return Response({'error': 'This account was not signed up using Google.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate JWT token for successful Google login
        refresh = RefreshToken.for_user(user)
        token = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        freelancer_status = hasattr(user, 'freelancer')
        client_status = hasattr(user, 'client')

        return Response({
            'message': 'Google login successful.',
            'token': token,
            'freelancer_status': freelancer_status,
            'client_status': client_status,
            'is_staff': user.is_staff,
            'email_verified': user.email_verified,
            'verified': user.verified,
        }, status=status.HTTP_200_OK)

    else:
        # Regular email-password login logic
        work_email = request.data.get('work_email')
        password = request.data.get('password')

        if not work_email or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Fetch user by email
        user = get_object_or_404(CustomUser, work_email=work_email)

        if not user.is_active:
            return Response({'error': 'Account is inactive.'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.email_verified:
            return Response({'error': 'Email is not verified.'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.verified:
            return Response({'error': 'Credentials not verified.'}, status=status.HTTP_401_UNAUTHORIZED)
        if user.suspend:
            return Response({'error': 'Account is suspended.'}, status=status.HTTP_401_UNAUTHORIZED)

        # Authenticate using password
        user = authenticate(username=user.username, password=password)
        if user:
            # Generate JWT token for regular login
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
                'email_verified': user.email_verified,
                'verified': user.verified,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)


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

        # Wallet.objects.create(user=request.user, balance=0)

        # Check if the user is a freelancer
        freelancer_status = hasattr(user_instance, 'freelancer')
        client_status = hasattr(user_instance, 'client')

        response_data = {
            'message': 'Otp Verified. your email is now verified',
            'freelancer_status': freelancer_status,
            'client_status': client_status,
            'is_staff': user_instance.is_staff,
            'email_verified': user_instance.email_verified,
            'verified': user_instance.verified,
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

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user(request):
    user = CustomUser.objects.get(id=request.user.id)
    serializer = UserStatusSerializer(user)
    return Response(serializer.data) 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def type(request):
    user = Freelancer.objects.get(id=request.user.id)
    serializer = TypeSerializer(user)
    return Response(serializer.data) 


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    user = CustomUser.objects.get(id=request.user.id)
    serializer =UserInfoSerializer(user)
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
def logout_view(request):
    serializer_class = LogoutSerializer
    serializer = serializer_class(data=request.data)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return Response(status=status.HTTP_204_NO_CONTENT)


import requests
from rest_framework.response import Response
from rest_framework.decorators import api_view

LINKEDIN_CLIENT_ID = '77iq9h80yfvu56'
LINKEDIN_CLIENT_SECRET = 'HNsKAZxGlcR7YoW0'
REDIRECT_URI = 'http://localhost:5173/auth/linkedin/callback'
LINKEDIN_TOKEN_URL = 'https://www.linkedin.com/oauth/v2/accessToken'
LINKEDIN_USER_INFO_URL = 'https://api.linkedin.com/v2/me'

LINKEDIN_EMAIL_URL = 'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))'

def fetch_linkedin_email(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    email_response = requests.get(LINKEDIN_EMAIL_URL, headers=headers)
    email_data = email_response.json()
    # Ensure email exists and handle potential missing email
    if email_response.status_code == 200 and 'elements' in email_data:
        email = email_data['elements'][0]['handle~']['emailAddress']
        return email
    return None  # Handle if email is not found


@api_view(["POST"])
def linkedin_callback(request):
    code = request.data.get('code')

    # Exchange the authorization code for an access token
    token_response = requests.post(LINKEDIN_TOKEN_URL, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': LINKEDIN_CLIENT_ID,
        'client_secret': LINKEDIN_CLIENT_SECRET,
    })

    token_data = token_response.json()
    access_token = token_data.get('access_token')

    if not access_token:
        return Response({"error": "LinkedIn token exchange failed"}, status=400)

    # Fetch user profile info
    headers = {'Authorization': f'Bearer {access_token}'}
    user_info_response = requests.get(LINKEDIN_USER_INFO_URL, headers=headers)
    user_info = user_info_response.json()

    first_name = user_info.get('localizedFirstName')
    last_name = user_info.get('localizedLastName')
    # Use LinkedIn's Email API to get the user's email (email might not be in the basic profile)
    email = user_info.get('emailAddress') 

    # Create the user in your database (similar to your Google OAuth logic)
    user_data = {
        'first_name': first_name,
        'last_name': last_name,
        'work_email': email,
        'username': f'{first_name.lower()}.{last_name.lower()}',
        'provider': 'linkedin',  # Mark as LinkedIn signup
        'provider_state': True,
    }

    # Check if the role is client or freelancer and use the appropriate serializer
    role = request.data.get('role')
    if role == 'client':
        serializer = ClientSerializer(data=user_data)
    elif role == 'freelancer':
        serializer = FreelancerSerializer(data=user_data)
    else:
        return Response({'error': 'Invalid role provided.'}, status=status.HTTP_400_BAD_REQUEST)

    if serializer.is_valid():
        user = serializer.save()
        user.provider = 'linkedin'
        user.provider_state = True
        user.email_verified = True

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        token = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        return Response({
            'message': 'LinkedIn signup successful',
            'token': token,
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

LINKEDIN_EMAIL_URL = 'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))'

def fetch_linkedin_email(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    email_response = requests.get(LINKEDIN_EMAIL_URL, headers=headers)
    email_data = email_response.json()
    # Ensure email exists and handle potential missing email
    if email_response.status_code == 200 and 'elements' in email_data:
        email = email_data['elements'][0]['handle~']['emailAddress']
        return email
    return None  # Handle if email is not found

@api_view(["POST"])
def linkedin_callback(request):
    code = request.data.get('code')

    # Exchange the authorization code for an access token
    token_response = requests.post(LINKEDIN_TOKEN_URL, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': LINKEDIN_CLIENT_ID,
        'client_secret': LINKEDIN_CLIENT_SECRET,
    })

    if token_response.status_code != 200:
        return Response({"error": "LinkedIn token exchange failed"}, status=400)

    token_data = token_response.json()
    access_token = token_data.get('access_token')

    if not access_token:
        return Response({"error": "LinkedIn token exchange failed"}, status=400)

    # Fetch user profile info
    headers = {'Authorization': f'Bearer {access_token}'}
    user_info_response = requests.get(LINKEDIN_USER_INFO_URL, headers=headers)
    
    if user_info_response.status_code != 200:
        return Response({"error": "Failed to fetch LinkedIn user profile"}, status=400)

    user_info = user_info_response.json()

    first_name = user_info.get('localizedFirstName')
    last_name = user_info.get('localizedLastName')

    # Fetch email separately using the function above
    email = fetch_linkedin_email(access_token)
    if not email:
        return Response({"error": "Unable to retrieve email from LinkedIn"}, status=400)

    # Create the user in your database (similar to your Google OAuth logic)
    user_data = {
        'first_name': first_name,
        'last_name': last_name,
        'work_email': email,
        'username': f'{first_name.lower()}.{last_name.lower()}',
        'provider': 'linkedin',  # Mark as LinkedIn signup
        'provider_state': True,
    }

    role = request.data.get('role')
    if role == 'client':
        serializer = ClientSerializer(data=user_data)
    elif role == 'freelancer':
        serializer = FreelancerSerializer(data=user_data)
    else:
        return Response({'error': 'Invalid role provided.'}, status=status.HTTP_400_BAD_REQUEST)

    if serializer.is_valid():
        user = serializer.save()
        user.provider = 'linkedin'
        user.provider_state = True
        user.email_verified = True

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        token = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

        return Response({
            'message': 'LinkedIn signup successful',
            'token': token,
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

