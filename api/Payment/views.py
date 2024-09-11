from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from api.models import Card, PayPal, Mpesa, Wallet
from .serializers import CardSerializer, PayPalSerializer, MpesaSerializer, WalletSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_wallet_balance(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
        serializer = WalletSerializer(wallet)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Wallet.DoesNotExist:
        return Response({'error': 'Wallet not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_card(request):
    serializer = CardSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_paypal(request):
    serializer = PayPalSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_mpesa(request):
    serializer = MpesaSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cards(request):
    cards = Card.objects.filter(user=request.user)
    serializer = CardSerializer(cards, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_paypals(request):
    paypals = PayPal.objects.filter(user=request.user)
    serializer = PayPalSerializer(paypals, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_mpesas(request):
    mpesas = Mpesa.objects.filter(user=request.user)
    serializer = MpesaSerializer(mpesas, many=True)
    return Response(serializer.data)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_card(request, id):
    try:
        card = Card.objects.get(id=id, user=request.user)
        card.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Card.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_paypal(request, id):
    try:
        paypal = PayPal.objects.get(id=id, user=request.user)
        paypal.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except PayPal.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_mpesa(request, id):
    try:
        mpesa = Mpesa.objects.get(id=id, user=request.user)
        mpesa.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Mpesa.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
