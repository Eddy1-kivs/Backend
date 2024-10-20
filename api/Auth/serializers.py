from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from api.models import Client, Freelancer, CustomUser, Subject, ServiceType, AssignmentType, Style, Language, Level, EducationlLevel, Test, LineSpacing
from rest_framework_simplejwt.tokens import RefreshToken,TokenError, OutstandingToken
from django.contrib.auth import password_validation
from django.contrib.auth.forms import PasswordChangeForm
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils.crypto import get_random_string

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password1 = serializers.CharField(required=True, write_only=True)
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value

    def validate(self, data):
        form = PasswordChangeForm(user=self.context['request'].user, data=data)
        if not form.is_valid():
            raise serializers.ValidationError(form.errors)
        return data

    def save(self):
        user = self.context['request'].user
        form = PasswordChangeForm(user=user, data=self.validated_data)
        if form.is_valid():
            form.save()
        return user
    

class ResetPasswordSerializer(serializers.Serializer):
    new_password1 = serializers.CharField(required=True, write_only=True)
    new_password2 = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        new_password1 = data.get('new_password1')
        new_password2 = data.get('new_password2')

        if new_password1 != new_password2:
            raise serializers.ValidationError("The two password fields didn't match.")

        password_validation.validate_password(new_password1, self.instance)

        return data

    def save(self, **kwargs):
        password = self.validated_data['new_password1']
        user = self.instance
        user.set_password(password)
        user.save()
        return user



class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']

class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType
        fields = ['id', 'name']


class AssignmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentType
        fields = ['id', 'name']

class LineSpacingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineSpacing
        fields = ['id', 'name']
 
class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name']

class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = ['id', 'name']

class EducationLevelSerializer(serializers.ModelSerializer): 
    class Meta:
        model = EducationlLevel
        fields = ['id', 'name']


class StyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Style
        fields = ['id', 'name']


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    otp = serializers.CharField(write_only=True, required=False)

    def create(self, validated_data):
        user = super().create(validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        errors = representation.get("errors")
        if errors:
            return {field: error[0] for field, error in errors.items()}
        return representation
    
class UserStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id', 
            'profile_image',
            'is_active', 
            'is_online', 
            'is_staff', 
            'is_superuser', 
            'freelancer_status', 
            'client_status', 
            'suspend', 
            
            'verified'
        ]

class TypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Freelancer
        fields = [
            'id',
            'is_writer',
            'username',
            'is_technical'
        ]
        
class UserInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields ='__all__'

class SupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'work_email', 'country', 'receive_news_option', 'is_staff', 'password', 'otp_code', 'CVs']
    
    def create(self, validated_data):
        if not validated_data.get('username'):
            validated_data['username'] = CustomUser().generate_unique_username()
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
         
class ClientSerializer(UserSerializer):
    class Meta:
        model = Client
        fields = [
            'id', 'first_name', 'last_name', 'work_email', 'country',
            'receive_news_option', 'username', 'client_status', 'password', 
            'otp', 'profile_image', 'provider', 'provider_uid'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'provider': {'read_only': True},  # This will only be set in case of OAuth
            'provider_uid': {'read_only': True},  # This too will be set for OAuth
        }

    def create(self, validated_data):
        # Check if the account is being created via OAuth provider
        if 'provider' not in validated_data:
            # Hash the password for regular sign-ups (non-OAuth)
            validated_data['password'] = make_password(validated_data['password'])
        
        return super().create(validated_data)


class FreelancerSerializer(UserSerializer):
    class Meta:
        model = Freelancer
        fields = ['id', 'first_name', 'last_name', 'country','profile_image',
                  'work_email', 'receive_news_option','freelancer_status', 'username', 'password', 'otp']

    def create(self, validated_data):
        # Ensure password is hashed
        validated_data['password'] = make_password(validated_data['password'])
        
        # Handle is_writer and is_technical based on type from the request data
        freelancer_type = self.context['request'].data.get('type')
        
        if freelancer_type == 'writer':
            validated_data['is_writer'] = True
            validated_data['is_technical'] = False
        elif freelancer_type == 'technical':
            validated_data['is_writer'] = False
            validated_data['is_technical'] = True

        return super().create(validated_data)
 

class ClientProfileSerializer(UserSerializer):
    class Meta:
        model = Client 
        fields = ['id', 'first_name', 'last_name', 'work_email', 'country', 
                  'receive_news_option', 'username', 'password', 'otp', 'county', 'city', 'is_active',
            'email_verified', 'timezone', 'profile_image']


class FreelancerProfileSerializer(UserSerializer):
    class Meta:
        model = Freelancer
        fields = ['id', 'first_name', 'last_name', 'country',
                  'work_email', 'receive_news_option', 'username', 'password']
        

class LogoutSerializer(serializers.Serializer):
    access = serializers.CharField()

    def validate(self, attrs):
        self.token = attrs.get('access')
        return attrs

    def save(self, **kwargs):
        try:
            if self.token:
                # Use OutstandingToken to blacklist the access token
                OutstandingToken.objects.filter(token=self.token).delete()
        except Exception:
            self.fail('fail')

    class Meta:
        error_messages = {
            'fail': 'Failed to blacklist token.'
        } 

        
class TestSerializer(serializers.ModelSerializer):
    freelancer = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = Test
        fields = '__all__'
        read_only_fields = ['freelancer']