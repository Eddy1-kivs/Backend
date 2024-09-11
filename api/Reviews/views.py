from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from api.models import Review
from .serializers import ReviewSerializer 
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_review(request):
    reviewer = request.user 
    recipient = request.data.get('recipient')
    job = request.data.get('job')
    comment = request.data.get('comment')
    rating = request.data.get('rating')
    
    try:
        recipient = reviewer.__class__.objects.get(id=recipient)
    except reviewer.__class__.DoesNotExist:
        return Response({'error': f'{reviewer.__class__.__name__} does not exist'}, status=404)
    
    data = {
        'recipient': recipient.id, 
        'reviewer': reviewer.id,
        'job': job,
        'comment': comment,
        'rating': rating,
    }
    
    serializer = ReviewSerializer(data=data)  # Use the data dictionary here
    if serializer.is_valid():
        # Create a new review instance
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_reviews(request):
    user = request.user  # Get the authenticated user
    
    # Filter reviews where the recipient is the authenticated user
    reviews = Review.objects.filter(recipient=user).order_by('-created_at')
    
    total_reviews = reviews.count()  # Calculate the total number of reviews
    
    if total_reviews > 0:
        total_rating = sum(review.rating for review in reviews)  # Calculate the total rating
        average_rating = total_rating / total_reviews  # Calculate the average rating
    else:
        average_rating = 0
    
    serializer = ReviewSerializer(reviews, many=True)
    
    response_data = {
        'reviews': serializer.data,
        'total_reviews': total_reviews,
        'average_rating': average_rating
    }
    
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def other_user_reviews(request, recipient_id):
    
    # Check if recipient_id is provided
    if recipient_id is None:
        return Response({'error': 'Recipient ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Filter reviews where the recipient matches the provided recipient_id
    reviews = Review.objects.filter(recipient_id=recipient_id).order_by('-created_at')
    
    total_reviews = reviews.count()  # Calculate the total number of reviews
    
    if total_reviews > 0:
        total_rating = sum(review.rating for review in reviews)  # Calculate the total rating
        average_rating = total_rating / total_reviews  # Calculate the average rating
    else:
        average_rating = 0
    
    serializer = ReviewSerializer(reviews, many=True)
    
    response_data = {
        'reviews': serializer.data,
        'total_reviews': total_reviews,
        'average_rating': average_rating
    }
    
    return Response(response_data, status=status.HTTP_200_OK)
