# views.py
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from api.models import Client, Proposal, Freelancer, JobSubmission, Revision, HiredFreelancer, RevisionReason, AmountPerPage, Invite, Transactions,Card, Mpesa
from .serializers import ProfileUpdateClientSerializer, ChangePasswordSerializer, JobPostSerializer, SkillSerializer, ExpertiseSerializer, JobSerializer, ProposalSerializer, JobSubmissionSerializer, RevisionSerializer,JobStatus, AmountPerPageSerializer, FreelancerListViewSerializer, FreelancerInviteSerializer
from rest_framework.permissions import IsAuthenticated
import bcrypt
from api.models import Skill, Expertise, Job 
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.db.models import Q
from django.core.mail import send_mail 
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from .payment import initiate_payment, verify_payment
from intasend import APIService
import os
import logging
import requests 

@api_view(['PUT']) 
@permission_classes([IsAuthenticated])
def update_client_profile(request):
    try:
        client = Client.objects.get(id=request.user.id)
    except Client.DoesNotExist:
        return Response({'error': 'Client not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProfileUpdateClientSerializer(client, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data)
    if serializer.is_valid():
        client = request.user

        # Check if the current password is a valid bcrypt hash
        try:
            bcrypt.checkpw(b'password', client.password.encode('utf-8'))
        except ValueError:
            return Response({'error': 'Invalid current password.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the new password and confirm password match
        new_password = serializer.validated_data['new_password']
        confirm_password = serializer.validated_data['confirm_password']
        if new_password != confirm_password:
            return Response({'error': 'New password and confirm password do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        # Generate a new salt and hash the new password
        hashed_new_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        # Store the hashed password in the database
        client.password = hashed_new_password.decode('utf-8')
        client.save()

        return Response({'message': 'Password changed successfully.'}, status=status.HTTP_200_OK)

    return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

# Initialize logger
logger = logging.getLogger(__name__)

# Function to get conversion rate from USD to KES
def get_conversion_rate():
    try:
        # API call to get the conversion rate from USD to KES
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
        response.raise_for_status()  # Raise an error for bad responses
        rates = response.json().get('rates', {})
        return rates.get('KES', 109.0)  # Fallback to a static rate if API fails
    except requests.RequestException as e:
        logger.error(f"Failed to fetch conversion rate: {e}")
        return 109.0  # Fallback rate

# Function to convert USD to KES
def convert_usd_to_kes(usd_amount):
    conversion_rate = get_conversion_rate()
    return usd_amount * conversion_rate



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def post_job(request):
    if request.method == 'POST':
        serializer = JobPostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                # Convert project_cost to a float
                project_cost = float(serializer.validated_data['project_cost'])
            except ValueError:
                return Response({'error': 'Invalid project cost provided.'}, status=status.HTTP_400_BAD_REQUEST)

            payment_method = request.data.get('payment_method')
            mpesa_number = request.data.get('mpesa_number')
            card_id = request.data.get('card_id')

            # Load API keys from environment variables
            publishable_key = os.getenv('INTASEND_PUBLIC_KEY')
            secret_key = os.getenv('INTASEND_SECRET_KEY')

            # Initialize IntaSend APIService with both secret key (token) and publishable key
            service = APIService(token=secret_key, publishable_key=publishable_key, test=False)

            # Handle M-Pesa payment
            if payment_method == 'mpesa':
                if not mpesa_number:
                    return Response({'error': 'No M-Pesa number provided.'}, status=status.HTTP_400_BAD_REQUEST)

                mpesa_account = Mpesa.objects.filter(phone_number=mpesa_number, user=request.user).first()
                if not mpesa_account:
                    return Response({'error': 'No valid M-Pesa account linked to your profile'}, status=status.HTTP_400_BAD_REQUEST)

                phone_number = mpesa_account.phone_number

                # Ensure the phone number starts with '254' by removing the '+' if present
                if phone_number.startswith('+'):
                    phone_number = phone_number[1:]  # Remove the '+'
                
                # Convert '07xxxxxxx' to '2547xxxxxxx' if needed
                if phone_number.startswith('07'):
                    phone_number = f"254{phone_number[1:]}"  # Convert '07xxxxxxx' to '2547xxxxxxx'

                # Convert the project cost from USD to KES
                amount_in_kes = convert_usd_to_kes(project_cost)

                try:
                    response = service.collect.mpesa_stk_push(
                        phone_number=phone_number,
                        email=request.user.email,
                        amount=project_cost,
                        narrative="Job Posting Payment"
                    )

                    logger.debug("IntaSend API STK Push Response: %s", response)
                    print("IntaSend API STK Push Response:", response)

                    invoice_id = response.get('invoice', {}).get('invoice_id')
                    invoice_state = response.get('invoice', {}).get('state', 'PENDING')

                    if not invoice_id:
                        logger.error("Invoice ID is missing in the response.")
                        return Response({'error': 'Failed to retrieve invoice ID from payment response.'}, status=status.HTTP_400_BAD_REQUEST)

                    if invoice_state != 'PENDING':
                        logger.error("Payment not in PENDING state.")
                        return Response({'error': 'Payment not initiated successfully.'}, status=status.HTTP_400_BAD_REQUEST)

                    transaction = Transactions.objects.create(
                        user=request.user,
                        amount=project_cost,
                        status='pending',
                        transaction_id=invoice_id
                    )

                    return Response({
                        'message': 'Payment initiated. Please confirm the payment on your phone.',
                        'invoice_id': invoice_id,
                    }, status=status.HTTP_200_OK)

                except Exception as e:
                    logger.exception("Error initiating payment")
                    print("Error initiating payment:", str(e))
                    return Response({'error': f'Failed to initiate payment: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

            # Handle Card payment using IntaSend's checkout API
            elif payment_method == 'card':
                if not card_id:
                    return Response({'error': 'No card selected for payment.'}, status=status.HTTP_400_BAD_REQUEST)

                card = Card.objects.filter(id=card_id, user=request.user).first()
                if not card:
                    return Response({'error': 'Selected card does not exist or is not linked to your profile.'}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    # Construct the payload for the checkout API
                    payload = {
                        "first_name": request.user.first_name,
                        "last_name": request.user.last_name,
                        "email": request.user.email,
                        "method": "CARD-PAYMENT",
                        "amount": project_cost,
                        "currency": "USD"  # Change this if necessary
                    }

                    headers = {
                        "Authorization": f"Bearer {secret_key}",
                        "Content-Type": "application/json"
                    }

                    # Send the request to IntaSend's checkout endpoint
                    response = requests.post(
                        'https://sandbox.intasend.com/api/v1/checkout/',
                        json=payload,
                        headers=headers
                    )

                    response_data = response.json()

                    if response.status_code == 200:
                        invoice_id = response_data.get('invoice_id')
                        transaction = Transactions.objects.create(
                            user=request.user,
                            amount=project_cost,
                            status='pending',
                            transaction_id=invoice_id
                        )
                        return Response({
                            'message': 'Payment initiated. Please complete the payment.',
                            'invoice_id': invoice_id,
                        }, status=status.HTTP_200_OK)
                    else:
                        logger.error(f"Error from IntaSend: {response_data}")
                        return Response({'error': 'Failed to initiate card payment.'}, status=status.HTTP_400_BAD_REQUEST)

                except Exception as e:
                    logger.exception("Error initiating payment")
                    print("Error initiating payment:", str(e))
                    return Response({'error': f'Failed to initiate payment: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response({'error': 'Invalid payment method selected.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_payment_and_post_job(request):
    invoice_id = request.data.get('invoice_id')  # Update to retrieve invoice_id
    transaction = Transactions.objects.filter(transaction_id=invoice_id).first()  # Filter by invoice_id

    if not transaction:
        return Response({'error': 'Invalid invoice ID or transaction already processed.'}, status=status.HTTP_400_BAD_REQUEST)

    if transaction.status != 'pending':
        return Response({'error': 'Transaction already processed or invalid.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Load API keys from environment variables
        publishable_key = os.getenv('INTASEND_PUBLIC_KEY')
        secret_key = os.getenv('INTASEND_SECRET_KEY')

        # Initialize IntaSend APIService with both secret key (token) and publishable key
        service = APIService(token=secret_key, publishable_key=publishable_key, test=False)

        # Verify the payment by checking the transaction status using the invoice_id
        response = service.collect.status(invoice_id)

        logger.debug("IntaSend Payment Verification Response: %s", response)
        print("IntaSend Payment Verification Response:", response)

        # Get the payment state from the response
        state = response.get('invoice', {}).get('state', 'PENDING')

        if state == 'COMPLETE':
            transaction.status = 'completed'
            transaction.save()

            # Post the job now that payment is confirmed
            serializer = JobPostSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                job = serializer.save(client=request.user.client)
                transaction.job = job
                transaction.save()

                return Response({
                    'message': 'Payment verified and job posted successfully.',
                    'job_details': serializer.data,
                    'invoice_details': response.get('invoice', {})
                }, status=status.HTTP_201_CREATED)
            else:
                transaction.status = 'failed'
                transaction.save()
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        elif state == 'PENDING':
            return Response({'error': 'Payment is still pending. Please wait and try again.'}, status=status.HTTP_202_ACCEPTED)
        else:
            transaction.status = 'failed'
            transaction.save()
            return Response({'error': 'Payment verification failed or payment not completed.'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Error during payment verification")
        print("Error during payment verification:", str(e))
        return Response({'error': f'Payment verification failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def verify_card_payment_and_post_job(request): 
    try:
        # Directly post the job using the provided data
        serializer = JobPostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid(): 
            job = serializer.save(client=request.user.client)
            job.paid = True  # Mark the job as paid
            job.save()

            return Response({
                'message': 'Job posted successfully.',
                'job_details': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.exception("Error posting job")
        return Response({'error': f'Job posting failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_skills(request):
    skills = Skill.objects.all()
    serializer = SkillSerializer(skills, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_expertise(request):
    expertise = Expertise.objects.all()
    serializer = ExpertiseSerializer(expertise, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_jobs(request):
    client_jobs = Job.objects.filter(client=request.user.client).order_by('-created_at')
    
    serializer = JobSerializer(client_jobs, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_jobs_completed(request):
    try:
        # Filter jobs where completed is True
        completed_jobs = HiredFreelancer.objects.filter(job__client=request.user.client, completed=True)
        serializer = JobSerializer([job_freelancer.job for job_freelancer in completed_jobs], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except HiredFreelancer.DoesNotExist:
        return Response({'message': 'No completed jobs found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_jobs_pending(request):
    try:
        # Filter jobs where pending is True
        pending_jobs = HiredFreelancer.objects.filter(job__client=request.user.client, pending=True)
        serializer = JobSerializer([job_freelancer.job for job_freelancer in pending_jobs], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except HiredFreelancer.DoesNotExist:
        return Response({'message': 'No pending jobs found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_jobs_with_proposals(request):
    try:
        # Retrieve the authenticated client
        client = request.user.client

        # Retrieve jobs posted by the authenticated client that have associated proposals
        # Exclude jobs where there are hired freelancers marked as started
        jobs_with_proposals = Job.objects.filter(
            client=client, 
            proposal__isnull=False
        ).exclude(
            hiredfreelancer__started=True
        ).distinct()

        # Serialize the queryset
        serializer = JobSerializer(jobs_with_proposals, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Job.DoesNotExist:
        return Response({'message': 'No jobs found with associated proposals'}, status=status.HTTP_404_NOT_FOUND)
    

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def invite_freelancer(request):
    serializer = FreelancerInviteSerializer(data=request.data)

    if serializer.is_valid():
        # Ensure the authenticated user is a client
        client = request.user.client

        # Retrieve freelancer and job objects
        freelancer_id = serializer.validated_data['freelancer_id']
        job_id = serializer.validated_data['job_id']

        # Check if the provided freelancer exists
        freelancer = get_object_or_404(Freelancer, id=freelancer_id)

        # Create the invitation
        Invite.objects.create(
            client=client, 
            freelancer=freelancer, 
            job_id=job_id, 
            message=serializer.validated_data.get('message', '')
        )

        # Send email to freelancer
        job = get_object_or_404(Job, id=job_id)
        frontend_url = settings.FRONTEND_URL
        job_url = f"{frontend_url}/job-detail/{job_id}/"
        subject = "You have been invited for a job"
        html_message = render_to_string('invite_email.html', {
            'freelancer': freelancer,
            'job': job,
            'job_url': job_url,
            'client': client,
            'message': serializer.validated_data.get('message', ''),
        })
        plain_message = strip_tags(html_message)
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = freelancer.work_email

        send_mail(subject, plain_message, from_email, [to_email], html_message=html_message)

        return Response({'message': 'Freelancer invited successfully.'}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

import boto3
from botocore.exceptions import NoCredentialsError
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

# Function to upload file to S3
def upload_to_s3(file, filename):
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME
    )

    try:
        s3.upload_fileobj(file, settings.AWS_STORAGE_BUCKET_NAME, filename)
        file_url = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{filename}"
        return file_url
    except NoCredentialsError:
        return None

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_profile_image(request):
    if 'file' not in request.FILES:
        return Response({"error": "No file uploaded"}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']
    filename = f"profile_images/{request.user.id}/{file.name}"

    file_url = upload_to_s3(file, filename)
    
    if file_url:
        return Response({"image_url": file_url}, status=status.HTTP_200_OK)
    else:
        return Response({"error": "Failed to upload image to S3"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_invited_jobs(request):
    try:
        # Retrieve the authenticated client
        client = request.user.client

        # Get all invites for the client
        invites = Invite.objects.filter(client=client)

        # Get the jobs that have been invited
        invited_jobs = Job.objects.filter(id__in=invites.values('job_id')).distinct()

        # Serialize the jobs
        serializer = JobSerializer(invited_jobs, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    except Job.DoesNotExist:
        return Response({'message': 'No invited jobs found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_counts(request):
    try:
        # Retrieve the authenticated client
        client = request.user.client

        # Count the number of proposals for jobs posted by the authenticated client
        proposals_count = Proposal.objects.filter(job__client=client)\
                                           .exclude(job__hiredfreelancer__started=True)\
                                           .count()

        # Count the number of completed jobs posted by the authenticated client
        completed_jobs_count = HiredFreelancer.objects.filter(job__client=client, completed=True).count()

        invites = Invite.objects.filter(client=client)

        # Get the jobs that have been invited
        invited_jobs = Job.objects.filter(id__in=invites.values('job_id')).count()

        # Count the number of jobs in progress posted by the authenticated client
        in_progress_jobs_count = HiredFreelancer.objects.filter(job__client=client, started=True, completed=False).count()

        # Count all jobs posted by the authenticated client
        all_jobs_count = Job.objects.filter(client=client).count()

        # Prepare response data
        data = {
            'proposals_count': proposals_count,
            'completed_jobs_count': completed_jobs_count,
            'in_progress_jobs_count': in_progress_jobs_count,
            'all_jobs_count': all_jobs_count,
            'invites': invited_jobs
        }

        return Response(data, status=status.HTTP_200_OK)
    except:
        return Response({'message': 'Failed to retrieve job counts'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_detail(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    job_serializer = JobSerializer(job, context={'request': request})

    proposals = Proposal.objects.filter(job=job)
    proposal_serializer = ProposalSerializer(proposals, many=True)

    # Check if the job is in the invite model for the requesting client and not accepted
    invite = Invite.objects.filter(job=job, client=request.user.client, accepted=False).first()
    is_invited = invite is not None

    serialized_data = job_serializer.data
    serialized_data['proposals'] = proposal_serializer.data
    serialized_data['num_proposals'] = proposals.count()
    serialized_data['is_invited'] = is_invited

    return Response(serialized_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def proposal_detail(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id)

    # Update the viewed status to True
    proposal.viewed = True
    proposal.save()

    proposal_serializer = ProposalSerializer(proposal)
    return Response(proposal_serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_client_profile_image(request):
    try:
        client = Client.objects.get(id=request.user.id)
    except Client.DoesNotExist:
        return Response({'error': 'Client not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Assuming you have a field named 'profile_image' in your client model
    client.profile_image = request.data.get('profile_image', None)

    # Save the changes
    client.save()

    serializer = ProfileUpdateClientSerializer(client)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_proposal(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id)
    if not proposal.declined:  # If declined is False
        proposal.accepted = True
    else:  # If declined is True
        proposal.declined = False
        proposal.accepted = True
    proposal.save()
    return Response({'message': 'Proposal accepted successfully'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_proposal(request, proposal_id):
    proposal = get_object_or_404(Proposal, id=proposal_id)
    if proposal.accepted:
        proposal.accepted = False
    proposal.declined = True
    proposal.save()
    return Response({'message': 'Proposal declined successfully'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_submissions(request, job_id):
    try:
        # Use .filter() to retrieve multiple objects and serialize them as a list
        job_submissions = JobSubmission.objects.filter(job_id=job_id)
        serializer = JobSubmissionSerializer(job_submissions, many=True)
        return Response(serializer.data)
    except JobSubmission.DoesNotExist:
        return Response({'message': 'Job submission not found'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_revision_submission(request, job_id):
    try:
        # Use filter to retrieve multiple revisions
        revision_submissions = Revision.objects.filter(job_id=job_id)
        
        # Serialize the queryset, many=True is used for multiple objects
        serializer = RevisionSerializer(revision_submissions, many=True)
        
        return Response(serializer.data, status=200)
    
    except Revision.DoesNotExist:
        return Response({'message': 'Revisions not found'}, status=404)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_status(request, job_id):
    try:
        job_status = HiredFreelancer.objects.get(job=job_id)
        serializer = JobStatus(job_status)
        return Response(serializer.data)
    except HiredFreelancer.DoesNotExist:
        return Response({'message': 'job does not exist'}, status=404)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def mark_submission_satisfied(request, job_id):
    try:
        # Retrieve all job submissions associated with the provided job_id
        job_submissions = JobSubmission.objects.filter(job_id=job_id)
        
        # Mark all associated job submissions as satisfied
        job_submissions.update(satisfied=True)

        # Update the associated hired freelancer's completed field to True
        hired_freelancer = HiredFreelancer.objects.get(job_id=job_id)
        hired_freelancer.completed = True
        hired_freelancer.pending = False
        hired_freelancer.save()

        return Response({'message': 'All job submissions marked as satisfied successfully'}, status=status.HTTP_200_OK)
    except HiredFreelancer.DoesNotExist:
        return Response({'error': 'Hired freelancer not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def request_revision(request, job_id):
    # Get the revision reason from the request data
    revision_reason = request.data.get('revisionNote', None)

    # Check if revision_reason is provided
    if not revision_reason:
        return Response({'error': 'Revision reason is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Retrieve the job submission associated with the provided job_id
        job_submission = JobSubmission.objects.get(job_id=job_id)
        
        # Update the job submission's need_revision field to True
        job_submission.need_revision = True
        job_submission.save()

        # Create a RevisionReason instance
        RevisionReason.objects.create(job=job_submission.job, reason=revision_reason)

        return Response({'message': 'Revision requested successfully'}, status=status.HTTP_200_OK)
    except JobSubmission.DoesNotExist:
        return Response({'error': 'Job submission not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([])
def get_amount_per_page(request):
    # Retrieve all instances of AmountPerPage
    amounts = AmountPerPage.objects.all()

    # Serialize the instances
    serializer = AmountPerPageSerializer(amounts, many=True)

    # Return the serialized data in the response
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_jobs_by_client(request):
    query = request.data.get('query', '')  # Get the search query from the request data
    
    # Filter jobs based on the search query
    client_jobs = Job.objects.filter(
        client=request.user.client,  # Filter by current client
        title__icontains=query  # Case-insensitive search for job title containing the query
    ).order_by('-created_at')

    serializer = JobSerializer(client_jobs, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)

from django.db.models import Avg

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def freelancer_list(request):
    freelancers = Freelancer.objects.all()
    serializer = FreelancerListViewSerializer(freelancers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def freelancer_detail(request, pk):
    try:
        freelancer = Freelancer.objects.get(pk=pk)
    except Freelancer.DoesNotExist:
        return Response({"message": "Freelancer not found."}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = FreelancerListViewSerializer(freelancer)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def freelancers_by_reviews(request):
    freelancers = Freelancer.objects.annotate(avg_reviews=Avg('recipient__rating')).order_by('-avg_reviews')
    serializer = FreelancerListViewSerializer(freelancers, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def active_freelancers(request):
    freelancers = Freelancer.objects.filter(suspend=False)
    serializer = FreelancerListViewSerializer(freelancers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_freelancers(request):
    query = request.GET.get('q', '')
    freelancers = Freelancer.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(username__icontains=query) |  # Added search by username
        Q(skills__name__icontains=query) |
        Q(subject__name__icontains=query)      # Added search by subject
    ).distinct()
    serializer = FreelancerListViewSerializer(freelancers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def freelancers_worked_with_client(request):
    try:
        client = Client.objects.get(id=request.user.id)
    except Client.DoesNotExist:
        return Response({'error': 'Client not found'}, status=404)

    hired_freelancers = HiredFreelancer.objects.filter(job__client=client).values_list('freelancer_id', flat=True)
    freelancers = Freelancer.objects.filter(id__in=hired_freelancers).distinct()
    serializer = FreelancerListViewSerializer(freelancers, many=True)
    return Response(serializer.data)
