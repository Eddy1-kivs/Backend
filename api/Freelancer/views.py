from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework import status
from api.models import Freelancer,Portfolio, Job, Proposal, HiredFreelancer, Client, Education, DeclinedJob, JobSubmission, Revision, RevisionReason, Review, Subject, AssignmentType, Invite
from .serializers import AfterRegisterSerializer, EducationFetchSerializer, UpdateVerificationCredentialsSerializer, FreelancerProfileSerializer, PortfolioSerializer, AllJobsSerializer, MatchingJobsSerializer, ProposalSerializer, HiredFreelancerSerializer,EducationSerializer, DeclinedJobSerializer, JobSubmissionSerializer, RevisionSerializer, RevisionReasonSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils import timezone
from django.db.models import Q, Avg, Count
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
 
@api_view(['PUT']) 
@permission_classes([IsAuthenticated])
def after_register(request):
    try:
        freelancer = Freelancer.objects.get(id=request.user.id)
    except Freelancer.DoesNotExist:
        return Response({'error': 'Freelancer not found.'}, status=status.HTTP_404_NOT_FOUND)
 
    serializer = AfterRegisterSerializer(freelancer, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_verification_credentials(request):
    try:
        freelancer = Freelancer.objects.get(id=request.user.id)
    except Freelancer.DoesNotExist:
        return Response({'error': 'Freelancer not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = UpdateVerificationCredentialsSerializer(freelancer, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_freelancer_profile(request):
    try:
        freelancer = Freelancer.objects.get(id=request.user.id)
    except Freelancer.DoesNotExist:
        return Response({'error': 'Freelancer not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = FreelancerProfileSerializer(freelancer)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile_image(request):
    try:
        freelancer = Freelancer.objects.get(id=request.user.id)
    except Freelancer.DoesNotExist:
        return Response({'error': 'Freelancer not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Assuming you have a field named 'profile_image' in your Freelancer model
    freelancer.profile_image = request.data.get('profile_image', None)

    # Save the changes
    freelancer.save()

    serializer = FreelancerProfileSerializer(freelancer)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_skills(request):
    serializer = FreelancerProfileSerializer(instance=request.user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def post_portfolio(request):
    serializer = PortfolioSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(freelancer=request.user.freelancer) 

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
 
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_portfolios(request):
    user = request.user
    portfolios = Portfolio.objects.filter(freelancer=user)
    serializer = PortfolioSerializer(portfolios, many=True)
    return Response(serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_portfolio(request, portfolio_id):
    try:
        portfolio = Portfolio.objects.get(id=portfolio_id)
    except Portfolio.DoesNotExist:
        return Response({"error": "Portfolio item does not exist."}, status=status.HTTP_404_NOT_FOUND)

    portfolio.delete()
    return Response({"success": "Portfolio item deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_jobs(request):
    freelancer_id = request.user.freelancer.id
    # Get jobs that are not assigned to any freelancer, for which the freelancer has not sent a proposal, and are not invited with declined=False
    jobs = Job.objects.exclude(
        Q(id__in=HiredFreelancer.objects.values_list('job_id', flat=True)) |
        Q(proposal__freelancer_id=freelancer_id) |
        Q(id__in=Invite.objects.filter(freelancer_id=freelancer_id, declined=False).values_list('job_id', flat=True))
    ).order_by('-created_at')
    serializer = AllJobsSerializer(jobs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_invited_jobs(request):
    freelancer_id = request.user.freelancer.id
    invited_jobs = Job.objects.filter(
        id__in=Invite.objects.filter(freelancer_id=freelancer_id, declined=False).values_list('job_id', flat=True)
    ).exclude(
        id__in=HiredFreelancer.objects.values_list('job_id', flat=True)
    ).order_by('-created_at')
    
    serializer = AllJobsSerializer(invited_jobs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_matching_jobs(request):
    freelancer_id = request.user.freelancer.id
    freelancer = Freelancer.objects.get(id=freelancer_id)
    freelancer_skills = freelancer.skills.all()
    freelancer_expertise = freelancer.expertise.all()
    freelancer_subjects = freelancer.subject.all()
    freelancer_assignment_types = freelancer.assignment_type.all()
    freelancer_service_types = freelancer.service_type.all()
    freelancer_languages = freelancer.language.all()

    matching_jobs = Job.objects.exclude(
        Q(id__in=HiredFreelancer.objects.values_list('job_id', flat=True)) |
        Q(proposal__freelancer_id=freelancer_id) |
        Q(id__in=Invite.objects.filter(freelancer_id=freelancer_id, declined=False).values_list('job_id', flat=True))
    ).filter(
        skills__in=freelancer_skills,
        expertise__in=freelancer_expertise,
        subjects__in=freelancer_subjects,
        assignment_types__in=freelancer_assignment_types,
        service_type__in=freelancer_service_types,
        languages__in=freelancer_languages
    ).distinct().order_by('-created_at')

    serializer = MatchingJobsSerializer(matching_jobs, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def search_jobs(request):
    title_query = request.data.get('title', '')
    freelancer_id = request.user.freelancer.id

    # Build the initial queryset
    job_query = Job.objects.exclude(
        Q(id__in=HiredFreelancer.objects.filter(started=True).values_list('job_id', flat=True)) |
        Q(proposal__freelancer_id=freelancer_id) |
        Q(id__in=Invite.objects.filter(freelancer_id=freelancer_id, declined=False).values_list('job_id', flat=True))
    )

    # Apply filters to include title, description, skills, and expertise
    if title_query:
        job_query = job_query.filter(
            Q(title__icontains=title_query) |
            Q(description__icontains=title_query) |
            Q(skills__name__icontains=title_query) |
            Q(expertise__expertise__icontains=title_query)
        ).distinct()

    # Serialize the job data
    jobs_data = AllJobsSerializer(job_query, many=True).data

    # Highlight the search term in the results
    highlighted_data = []
    for job in jobs_data:
        for field in ['title', 'description']:
            if title_query in job[field]:
                job[field] = job[field].replace(title_query, f"<mark>{title_query}</mark>")
        highlighted_data.append(job)

    return Response(highlighted_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def accept_invite(request, invite_id):
    try:
        invite = Invite.objects.get(id=invite_id, freelancer=request.user.freelancer)
    except Invite.DoesNotExist:
        return Response({'error': 'Invite not found.'}, status=status.HTTP_404_NOT_FOUND)

    invite.accepted = True
    invite.declined = False
    invite.save()

    # Create a new HiredFreelancer record
    HiredFreelancer.objects.create(
        job=invite.job,
        freelancer=invite.freelancer,
        started=True,  # Mark the job as started, adjust as per your requirements
        pending=True,
    )

    # Send email notification to the client
    client_email = invite.client.work_email  # Assuming client has a related user model with an email field
    subject = 'Invite Accepted: Job Started'
    html_message = render_to_string('invite_accepted.html', {'job': invite.job, 'freelancer': invite.freelancer})
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [client_email]

    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

    return Response({'message': 'Invite accepted successfully.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_invite(request, invite_id):
    try:
        invite = Invite.objects.get(id=invite_id, freelancer=request.user.freelancer)
    except Invite.DoesNotExist:
        return Response({'error': 'Invite not found.'}, status=status.HTTP_404_NOT_FOUND)

    invite.accepted = False
    invite.declined = True
    invite.declined_reason = request.data.get('declined_reason', '')
    invite.save()

    # Send email notification to the client
    client_email = invite.client.work_email  # Assuming client has a related user model with an email field
    subject = 'Invite Declined: Freelancer Declined Your Invite'
    html_message = render_to_string('invite_declined.html', {
        'job': invite.job,
        'freelancer': invite.freelancer,
        'declined_reason': invite.declined_reason
    })
    plain_message = strip_tags(html_message)
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [client_email]

    send_mail(subject, plain_message, from_email, recipient_list, html_message=html_message)

    return Response({'message': 'Invite declined successfully.'}, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_details(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
    except Job.DoesNotExist:
        return Response({'error': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Check if the job is in the Invite model with declined as false
    invite = Invite.objects.filter(job=job, declined=False).first()

    serializer = AllJobsSerializer(job)
    response_data = serializer.data
    response_data['is_invited'] = invite is not None
    if invite:
        response_data['invite_id'] = invite.id

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def create_proposal(request):
    serializer = ProposalSerializer(data=request.data, context={'request': request})

    if serializer.is_valid():
        # Get the current authenticated user's freelancer instance
        freelancer_instance = request.user.freelancer

        # Assuming request.data contains the job_id
        job_id = request.data.get('job')
        job = Job.objects.get(id=job_id)

        # Populate freelancer field in the serializer with the current user's freelancer instance
        serializer.validated_data['freelancer'] = freelancer_instance
        serializer.validated_data['job'] = job

        # Save the proposal
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_proposals(request):
    # Get all proposals for the current freelancer
    proposals = Proposal.objects.filter(freelancer=request.user.freelancer).order_by('-submitted_at')

    # Filter out proposals that are already started
    filtered_proposals = []
    for proposal in proposals:
        # Check if there exists any HiredFreelancer instance for this proposal with started=True
        if not HiredFreelancer.objects.filter(job=proposal.job, freelancer=request.user.freelancer, started=True).exists():
            filtered_proposals.append(proposal)

    # Serialize the data
    serializer = ProposalSerializer(filtered_proposals, many=True)
    
    # Count the number of filtered proposals
    num_proposals = len(filtered_proposals)

    # Add the number of proposals to the response data
    data = {
        'proposals': serializer.data,
        'num_proposals': num_proposals
    }

    return Response(data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_proposal_details(request, proposal_id):
    try:
        proposal = Proposal.objects.get(id=proposal_id, freelancer=request.user.freelancer)
    except Proposal.DoesNotExist:
        return Response({'error': 'Proposal not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProposalSerializer(proposal)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_proposal(request, proposal_id):
    try:
        proposal = Proposal.objects.get(id=proposal_id, freelancer=request.user.freelancer)
    except Proposal.DoesNotExist:
        return Response({'error': 'Proposal not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = ProposalSerializer(proposal, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_proposal(request, proposal_id):
    try:
        proposal = Proposal.objects.get(id=proposal_id, freelancer=request.user.freelancer)
    except Proposal.DoesNotExist:
        return Response({'error': 'Proposal not found.'}, status=status.HTTP_404_NOT_FOUND)

    proposal.delete()
    return Response({'message': 'Proposal deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def decline_job(request):
    proposal_id = request.data.get('proposal_id')
    if proposal_id is None:
        return Response({'error': 'Proposal ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Ensure the proposal exists and belongs to the current user's freelancer instance
        proposal = Proposal.objects.get(id=proposal_id, freelancer=request.user.freelancer)
    except Proposal.DoesNotExist:
        return Response({'error': 'Proposal not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'POST':
        # Create an instance of the DeclinedJobSerializer with the data from the request
        serializer = DeclinedJobSerializer(data=request.data)

        if serializer.is_valid():
            # Save the serializer instance to create a new DeclinedJob object
            declined_job = serializer.save(
                freelancer=request.user.freelancer,
                proposal_id=proposal_id,
                declined_at=timezone.now()
            )
            # Optionally, set the reason field separately based on request data
            declined_job.reason = request.data.get('reason', '')
            declined_job.save()

            # Delete the proposal
            proposal.delete()

            return Response({'message': 'Job proposal declined successfully.'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({'error': 'Method not allowed.'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def start_work(request):
    try:
        # Get the current authenticated user's freelancer instance
        freelancer_instance = request.user.freelancer

        # Assuming request.data contains the job_id
        job_id = request.data.get('job_id')
        job = Job.objects.get(id=job_id)

        # Create or update the HiredFreelancer instance
        hired_freelancer, created = HiredFreelancer.objects.get_or_create(
            freelancer=freelancer_instance,
            job=job,
            defaults={
                'started_at': timezone.now(),
                'started': True,
                'pending': True,
            }
        )

        # If the instance already exists, update the fields
        if not created:
            hired_freelancer.started_at = timezone.now()
            hired_freelancer.started = True
            hired_freelancer.pending = True
            hired_freelancer.save()

        # Serialize the HiredFreelancer instance
        serializer = HiredFreelancerSerializer(hired_freelancer)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_freelancer_tasks(request): 
    try:
        freelancer = request.user.freelancer 
        
        tasks = HiredFreelancer.objects.filter(freelancer=freelancer).order_by('-started_at')
        
        serializer = HiredFreelancerSerializer(tasks, many=True)
        
        return Response({
            'tasks': serializer.data,
            'num_tasks': tasks.count()  # Return the count of all tasks
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_pending_jobs(request):
    try:
        freelancer = request.user.freelancer
        
        pending_jobs = HiredFreelancer.objects.filter(freelancer=freelancer, pending=True).order_by('-started_at')
        serializer = HiredFreelancerSerializer(pending_jobs, many=True)
        return Response({
            'pending_jobs': serializer.data,
            'num_pending_jobs': pending_jobs.count()  # Return the count of filtered pending jobs
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_completed_jobs(request):
    try:
        freelancer = request.user.freelancer
        # Fetching all completed jobs for the freelancer
        completed_jobs = HiredFreelancer.objects.filter(freelancer=freelancer, completed=True).order_by('-finished_at')
        serializer = HiredFreelancerSerializer(completed_jobs, many=True)
        return Response({
            'completed_jobs': serializer.data,
            'num_completed': completed_jobs.count() 
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_detail(request, job_id):
    try:
        # Fetching the job with the provided ID belonging to the current user's freelancer instance
        job = HiredFreelancer.objects.get(job=job_id, freelancer=request.user.freelancer)
        serializer = HiredFreelancerSerializer(job)  # No need for many=True
        return Response(serializer.data, status=status.HTTP_200_OK)
    except HiredFreelancer.DoesNotExist:
        return Response({'error': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def add_education(request):
    serializer = EducationSerializer(data=request.data)
 
    if serializer.is_valid():
        # Set the freelancer field to the current authenticated user
        serializer.save(freelancer=request.user.freelancer) 

        # Save the education instance 
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_education(request):
    # Get the education items for the current user
    education_items = Education.objects.filter(freelancer=request.user)
    serializer = EducationFetchSerializer(education_items, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_education(request, education_id):
    try:
        # Check if the education item exists and belongs to the current user
        education_item = Education.objects.get(id=education_id, freelancer=request.user)
    except Education.DoesNotExist:
        return Response({'error': 'Education item not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Delete the education item
    education_item.delete()

    return Response({'message': 'Education item deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_job(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
        freelancer = request.user.freelancer  # Assuming the Freelancer is related to User
    except Job.DoesNotExist:
        return Response({'error': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Freelancer.DoesNotExist:
        return Response({'error': 'Freelancer not found.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = JobSubmissionSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(job=job, freelancer=freelancer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def submit_revision(request, job_id):
    try:
        job = Job.objects.get(id=job_id)
        freelancer = request.user.freelancer
    except Job.DoesNotExist:
        return Response({'error': 'Job not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Freelancer.DoesNotExist:
        return Response({'error': 'Freelancer not found.'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = RevisionSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(job=job, freelancer=freelancer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def revision_reason(request, job_id):
    try:
        revision_reason = RevisionReason.objects.get(job_id=job_id)
        serializer = RevisionReasonSerializer(revision_reason)
        return Response(serializer.data)
    except RevisionReason.DoesNotExist:
        return Response({'message': 'Reason not found'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_submission(request, job_id):
    try:
        job_submission = JobSubmission.objects.get(job_id=job_id, freelancer=request.user.freelancer)
        serializer = JobSubmissionSerializer(job_submission)
        return Response(serializer.data)
    except JobSubmission.DoesNotExist:
        return Response({'message': 'Job submission not found'}, status=404)
     

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_stats(request):
    # Get the user's ID
    user_id = request.user.id

    # Get the proposals sent by the user
    proposals = Proposal.objects.filter(freelancer_id=user_id)

    # Filter the proposals based on the condition
    filtered_proposals = []
    for proposal in proposals:
        # Check if there exists any HiredFreelancer instance for this proposal with started=True
        if not HiredFreelancer.objects.filter(job=proposal.job, freelancer=request.user.freelancer, started=True).exists():
            filtered_proposals.append(proposal)

    # Get the number of filtered proposals
    num_proposals_sent = len(filtered_proposals)

    # Get the number of pending jobs for the user
    num_pending_jobs = HiredFreelancer.objects.filter(freelancer_id=user_id, pending=True).count()

    # Get the number of completed jobs for the user
    num_completed_jobs = HiredFreelancer.objects.filter(freelancer_id=user_id, completed=True).count()

    invited_jobs = Job.objects.filter(
        id__in=Invite.objects.filter(freelancer_id=user_id, declined=False).values_list('job_id', flat=True)
    ).count()

    # Calculate the total number of tasks completed by the user (pending + completed)
    num_tasks_completed = num_pending_jobs + num_completed_jobs

    # Calculate the average reviews and the number of reviews for the user
    reviews = Review.objects.filter(recipient=request.user).aggregate(average_rating=Avg('rating'), num_reviews=Count('id'))
    average_reviews = reviews['average_rating']
    num_reviews = reviews['num_reviews']

    # Construct the response data
    data = {
        'num_proposals_sent': num_proposals_sent,
        'num_pending_jobs': num_pending_jobs,
        'num_completed_jobs': num_completed_jobs,
        'invites': invited_jobs,
        'num_tasks_completed': num_tasks_completed,
        'average_reviews': average_reviews,
        'num_reviews': num_reviews
    }

    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def freelancer_stats(request, freelancer_id):
    # Get the proposals sent by the freelancer
    proposals = Proposal.objects.filter(freelancer=freelancer_id)

    # Filter the proposals based on the condition
    filtered_proposals = []
    for proposal in proposals:
        if not HiredFreelancer.objects.filter(job=proposal.job, freelancer=freelancer_id, started=True).exists():
            filtered_proposals.append(proposal)

    # Get the number of filtered proposals
    num_proposals_sent = len(filtered_proposals)

    # Get the number of pending jobs for the freelancer
    num_pending_jobs = HiredFreelancer.objects.filter(freelancer=freelancer_id, pending=True).count()

    # Get the number of completed jobs for the freelancer
    num_completed_jobs = HiredFreelancer.objects.filter(freelancer=freelancer_id, completed=True).count()

    # Calculate the total number of tasks completed by the freelancer (pending + completed)
    num_tasks_completed = num_pending_jobs + num_completed_jobs

    # Calculate the average reviews and the number of reviews for the freelancer
    reviews = Review.objects.filter(recipient__freelancer=freelancer_id).aggregate(average_rating=Avg('rating'), num_reviews=Count('id'))
    average_reviews = reviews['average_rating']
    num_reviews = reviews['num_reviews']

    # Get all completed jobs by the freelancer
    completed_jobs = HiredFreelancer.objects.filter(freelancer=freelancer_id, completed=True)

    invited_jobs = Job.objects.filter(
        id__in=Invite.objects.filter(freelancer_id=freelancer_id, declined=False).values_list('job_id', flat=True)
    ).count()

    # Get the subjects and assignment types for completed jobs
    subjects_stats = {}
    assignment_types_stats = {}

    for job in completed_jobs:
        # Increment subject count
        for subject in job.job.subjects.all():
            # Update subjects_stats to include the total number of jobs related to each subject
            subjects_stats[subject.name] = {
                'total_jobs': Subject.objects.filter(name=subject.name).annotate(total_jobs=Count('job')).first().total_jobs,
                'completed_jobs': subjects_stats.get(subject.name, {'total_jobs': 0, 'completed_jobs': 0})['completed_jobs'] + 1
            }

        # Increment assignment type count
        for assignment_type in job.job.assignment_types.all():
            assignment_types_stats[assignment_type.name] = assignment_types_stats.get(assignment_type.name, 0) + 1

    # Construct the response data
    data = {
        'num_proposals_sent': num_proposals_sent,
        'num_pending_jobs': num_pending_jobs,
        'num_completed_jobs': num_completed_jobs,
        'num_tasks_completed': num_tasks_completed,
        'average_reviews': average_reviews,
        'num_reviews': num_reviews,
        'invites': invited_jobs,
        'subjects_stats': subjects_stats,
        'assignment_types_stats': assignment_types_stats
    }

    return Response(data)
