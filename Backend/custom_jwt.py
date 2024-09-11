from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from api.models import Client


class CustomJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        client_id = validated_token[api_settings.USER_ID_CLAIM]

        # Try to convert client_id to an integer
        try:
            client = Client.objects.get(id=int(client_id))
        except (ValueError, Client.DoesNotExist):
            # If conversion to integer fails or client does not exist, assume it's a UUID
            client = Client.objects.get(id=client_id)

        return client
