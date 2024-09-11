from rest_framework import serializers
from api.models import Card, PayPal, Mpesa, Wallet

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'user', 'cardholder_name', 'card_number', 'expiration_date', 'cvv', 'card_type']
        read_only_fields = ['user']  # Make the user field read-only

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super(CardSerializer, self).create(validated_data)

class PayPalSerializer(serializers.ModelSerializer):
    class Meta:
        model = PayPal
        fields = ['id', 'user', 'email']
        read_only_fields = ['user']  # Make the user field read-only

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super(PayPalSerializer, self).create(validated_data)

class MpesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mpesa
        fields = ['id', 'user', 'phone_number']
        read_only_fields = ['user']  # Make the user field read-only

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super(MpesaSerializer, self).create(validated_data)

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['user', 'balance']
        read_only_fields = ['user', 'balance']  # Make the user and balance fields read-only
