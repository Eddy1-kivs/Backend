from rest_framework import serializers
from api.models import CustomUser, Freelancer, Suspension, HiredFreelancer, Client

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = '__all__'

class FreelancerSerializer(serializers.ModelSerializer):

    class Meta:
        model = Freelancer
        fields = '__all__'

class ClientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = '__all__'

class SuspensionSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.work_email')

    class Meta:
        model = Suspension
        fields = ['id', 'user', 'suspension_reason', 'suspension_days', 'suspension_end_date']
 
class HiredFreelancerSerializer(serializers.ModelSerializer):
    class Meta:
        model = HiredFreelancer
        fields = '__all__'