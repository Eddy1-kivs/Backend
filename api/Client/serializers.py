# serializers.py
from rest_framework import serializers
from api.models import Client, Job, Skill, Expertise,Freelancer, Proposal, UploadFile, JobSubmission, Revision, HiredFreelancer,  RevisionReason, AmountPerPage,Review, Subject, Language, AssignmentType, ServiceType, LineSpacing, Invite, Style, Level,  EducationlLevel

from rest_framework.response import Response
from rest_framework import status  
from datetime import datetime , timedelta, time
from django.utils import timezone
from django.template.defaultfilters import date as _date
import mimetypes
import html2text
from django.db.models import Avg, Count

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill 
        fields = '__all__'

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = '__all__'

class FreelancerInviteSerializer(serializers.Serializer):
    freelancer_id = serializers.UUIDField()
    job_id = serializers.IntegerField()
    message = serializers.CharField(max_length=1000, required=False)

    def validate(self, data):
        # Check if the freelancer exists
        freelancer = Freelancer.objects.filter(id=data['freelancer_id']).exists()
        if not freelancer:
            raise serializers.ValidationError("Freelancer not found.")
        
        # Check if the job exists
        job = Job.objects.filter(id=data['job_id']).exists()
        if not job:
            raise serializers.ValidationError("Job not found.")
        
        return data

class ExpertiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expertise
        fields = ['id', 'expertise']

# Add serializers for Language, AssignmentType, and ServiceType
class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'

class AssignmentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssignmentType
        fields = '__all__'

class LineSpacingSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineSpacing
        fields = '__all__'

class ServiceTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceType
        fields = '__all__'

class FreelancerListViewSerializer(serializers.ModelSerializer):
    average_reviews = serializers.SerializerMethodField()
    total_reviews = serializers.SerializerMethodField()
    completed_jobs = serializers.SerializerMethodField()
    pending_tasks = serializers.SerializerMethodField()
    skills = SkillSerializer(many=True, read_only=True)
    subject = SubjectSerializer(read_only=True, many=True)
    expertise = ExpertiseSerializer(many=True, read_only=True)
    # Add new fields
    language = LanguageSerializer(many=True, read_only=True)
    assignment_type = AssignmentTypeSerializer(many=True, read_only=True)
    service_type = ServiceTypeSerializer(many=True, read_only=True)

    class Meta:
        model = Freelancer
        fields = ['id', 'first_name', 'last_name', 'username', 'skills', 'expertise', 'bio', 'language', 'assignment_type', 'service_type', 'subject', 'profile_image', 'email_verified', 'suspend',
                  'average_reviews', 'total_reviews', 'completed_jobs', 'pending_tasks']

    def get_average_reviews(self, obj):
        reviews_avg = Review.objects.filter(recipient=obj).aggregate(Avg('rating'))['rating__avg']
        return reviews_avg if reviews_avg else 0.0

    def get_total_reviews(self, obj):
        return Review.objects.filter(recipient=obj).count()

    def get_completed_jobs(self, obj):
        return HiredFreelancer.objects.filter(freelancer=obj, completed=True).count()

    def get_pending_tasks(self, obj):
        return HiredFreelancer.objects.filter(freelancer=obj, completed=False).count()



class AmountPerPageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmountPerPage
        fields = ['amount']
class ProfileUpdateClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['profile_image', 'username', 'first_name', 'last_name', 'timezone', 'county', 'city', 'country']

class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

class UploadFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadFile
        fields = ['id', 'file', 'uploaded_at']

# class JobPostSerializer(serializers.ModelSerializer):
#     files = UploadFileSerializer(many=True, read_only=True)
#     skills = serializers.PrimaryKeyRelatedField(queryset=Skill.objects.all(), many=True)
#     expertise = serializers.PrimaryKeyRelatedField(queryset=Expertise.objects.all(), many=True)
#     languages = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True)
#     service_type = serializers.PrimaryKeyRelatedField(queryset=ServiceType.objects.all(), many=True)
#     subjects = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), many=True)
#     assignment_types = serializers.PrimaryKeyRelatedField(queryset=AssignmentType.objects.all(), many=True)
#     style = serializers.PrimaryKeyRelatedField(queryset=Style.objects.all(), many=True)
#     levels = serializers.PrimaryKeyRelatedField(queryset=Level.objects.all(), many=True)
#     education_levels = serializers.PrimaryKeyRelatedField(queryset=EducationlLevel.objects.all(), many=True)
#     line_spacing = serializers.PrimaryKeyRelatedField(queryset=LineSpacing.objects.all(), many=True)

#     # New field for job type
#     job_type = serializers.ChoiceField(choices=['writing', 'technical'], required=True)

#     class Meta:
#         model = Job
#         fields = [
#             'id', 'title', 'description', 'files', 'due_date', 'num_pages', 'words', 'project_cost',
#             'expertise', 'skills', 'created_at', 'service', 'languages', 'service_type', 'subjects',
#             'assignment_types', 'style', 'levels', 'education_levels', 'line_spacing', 'page_abstract',
#             'printable_sources', 'detailed_outline', 'job_type'  # Include job_type in fields
#         ]
#         extra_kwargs = {
#             'line_spacing': {'error_messages': {'required': 'Spacing is required'}},
#             'title': {'error_messages': {'required': 'Title is required.'}},
#             'description': {'error_messages': {'required': 'Description is required.'}},
#             'num_pages': {'error_messages': {'invalid': 'Invalid number of pages.'}},
#             'project_cost': {'error_messages': {'required': 'Project cost is required.'}},
#             'expertise': {'error_messages': {'empty': 'At least one expertise is required.'}},
#             'skills': {'error_messages': {'empty': 'At least one skill is required.'}},
#             'languages': {'error_messages': {'invalid': 'Invalid language.'}},
#             'service_type': {'error_messages': {'invalid': 'Invalid service type.'}},
#             'subjects': {'error_messages': {'invalid': 'Invalid subject.'}},
#             'assignment_types': {'error_messages': {'invalid': 'Invalid assignment type.'}},
#             'style': {'error_messages': {'invalid': 'Invalid style.'}},
#             'levels': {'error_messages': {'empty': 'A profession level is required.'}},
#             'education_levels': {'error_messages': {'empty': 'An education level is required.'}},
#         }

#     def create(self, validated_data):
#         job_type = validated_data.pop('job_type')  # Get the job type
#         # rest of the data
#         files_data = self.context['request'].FILES
#         expertise_data = validated_data.pop('expertise', [])
#         skills_data = validated_data.pop('skills', [])
#         languages_data = validated_data.pop('languages', [])
#         service_type_data = validated_data.pop('service_type', [])
#         subjects_data = validated_data.pop('subjects', [])
#         style_data = validated_data.pop('style', [])
#         line_spacing_data = validated_data.pop('line_spacing', [])
#         assignment_types_data = validated_data.pop('assignment_types', [])
#         levels = validated_data.pop('levels', [])
#         education_levels = validated_data.pop('education_levels', [])

#         # Convert HTML description to plain text
#         html_description = validated_data.get('description', '')
#         plain_text_description = html2text.html2text(html_description)
#         validated_data['description'] = plain_text_description

#         # Create job object with base validated data
#         job = Job.objects.create(**validated_data)

#         # Set the job type
#         if job_type == 'writing':
#             job.is_writing = True
#         elif job_type == 'technical':
#             job.is_technical = True

#         job.save()

#         # Continue with setting up relationships
#         for file_data in files_data.getlist('files'):
#             upload_file = UploadFile.objects.create(file=file_data)
#             job.files.add(upload_file)

#         job.languages.set(languages_data)
#         job.line_spacing.set(line_spacing_data)
#         job.service_type.set(service_type_data)
#         job.subjects.set(subjects_data)
#         job.style.set(style_data)
#         job.assignment_types.set(assignment_types_data)
#         job.levels.set(levels)
#         job.education_levels.set(education_levels)

#         if expertise_data:
#             job.expertise.set(expertise_data)
#         if skills_data:
#             job.skills.set(skills_data)

#         return job


class JobPostSerializer(serializers.ModelSerializer):
    files = UploadFileSerializer(many=True, read_only=True)
    skills = serializers.PrimaryKeyRelatedField(queryset=Skill.objects.all(), many=True)
    expertise = serializers.PrimaryKeyRelatedField(queryset=Expertise.objects.all(), many=True)
    languages = serializers.PrimaryKeyRelatedField(queryset=Language.objects.all(), many=True)
    service_type = serializers.PrimaryKeyRelatedField(queryset=ServiceType.objects.all(), many=True)
    subjects = serializers.PrimaryKeyRelatedField(queryset=Subject.objects.all(), many=True)
    assignment_types = serializers.PrimaryKeyRelatedField(queryset=AssignmentType.objects.all(), many=True)
    style = serializers.PrimaryKeyRelatedField(queryset=Style.objects.all(), many=True)
    levels = serializers.PrimaryKeyRelatedField(queryset=Level.objects.all(), many=True)
    education_levels = serializers.PrimaryKeyRelatedField(queryset=EducationlLevel.objects.all(), many=True)
    line_spacing = serializers.PrimaryKeyRelatedField(queryset=LineSpacing.objects.all(), many=True)
    
    

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'description', 'files', 'due_date', 'num_pages', 'words', 'project_cost',
            'expertise', 'skills', 'created_at', 'service',
            'languages', 'service_type', 'subjects', 'assignment_types', 'style', 'levels', 'education_levels',
            'line_spacing', 'page_abstract', 'printable_sources', 'detailed_outline'
        ]
        
        extra_kwargs = {
            'line_spacing': {'error_messages': {'required': 'Spacing is required'}},
            'title': {'error_messages': {'required': 'Title is required.'}},
            'description': {'error_messages': {'required': 'Description is required.'}},
            'num_pages': {'error_messages': {'invalid': 'Invalid number of pages.'}},
            'project_cost': {'error_messages': {'required': 'Project cost is required.'}},
            'expertise': {'error_messages': {'empty': 'At least one expertise is required.'}},
            'skills': {'error_messages': {'empty': 'At least one skill is required.'}},
            'languages': {'error_messages': {'invalid': 'Invalid language.'}},
            'service_type': {'error_messages': {'invalid': 'Invalid service type.'}},
            'subjects': {'error_messages': {'invalid': 'Invalid subject.'}},
            'assignment_types': {'error_messages': {'invalid': 'Invalid assignment type.'}},
            'style': {'error_messages': {'invalid': 'Invalid style.'}},
            'levels': {'error_messages': {'empty': 'A profession level is required.'}},
            'education_levels': {'error_messages': {'empty': 'An education level is required.'}},
        }

    def create(self, validated_data):
        files_data = self.context['request'].FILES
        expertise_data = validated_data.pop('expertise', [])
        skills_data = validated_data.pop('skills', [])
        languages_data = validated_data.pop('languages', [])
        service_type_data = validated_data.pop('service_type', [])
        subjects_data = validated_data.pop('subjects', [])
        style_data = validated_data.pop('style', [])
        line_spacing_data = validated_data.pop('line_spacing', [])
        assignment_types_data = validated_data.pop('assignment_types', [])
        levels = validated_data.pop('levels', [])
        education_levels = validated_data.pop('education_levels', [])

        # Convert HTML description to plain text
        html_description = validated_data.get('description', '')
        plain_text_description = html2text.html2text(html_description)
        validated_data['description'] = plain_text_description

        job = Job.objects.create(**validated_data)

        for file_data in files_data.getlist('files'):
            upload_file = UploadFile.objects.create(file=file_data)
            job.files.add(upload_file)

        job.languages.set(languages_data)
        job.line_spacing.set(line_spacing_data)
        job.service_type.set(service_type_data)
        job.subjects.set(subjects_data)
        job.style.set(style_data)
        job.assignment_types.set(assignment_types_data)
        job.levels.set(levels)
        job.education_levels.set(education_levels)

        if expertise_data:
            job.expertise.set(expertise_data)

        if skills_data:
            job.skills.set(skills_data)

        
        return job

class ProposalSerializer(serializers.ModelSerializer):
    freelancer_username = serializers.CharField(source='freelancer.username', read_only=True)
    freelancer_profile_image = serializers.URLField(source='freelancer.profile_image', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    cover_letter = serializers.CharField()
    bid_amount = serializers.DecimalField(max_digits=10, decimal_places=2, default='1')
    submitted_at = serializers.SerializerMethodField()
    attachment = serializers.FileField(source='attachment.url', read_only=True)
    viewed = serializers.BooleanField(default=False)
    viewed_at = serializers.SerializerMethodField() 
    skills = serializers.StringRelatedField(source='freelancer.skills', many=True)
    expertise = serializers.StringRelatedField(source='freelancer.expertise', many=True)
    
    language = serializers.StringRelatedField(source='freelancer.language', many=True)
    assignment_type = serializers.StringRelatedField(source='freelancer.assignment_type', many=True)
    service_type = serializers.StringRelatedField(source='freelancer.service_type', many=True)
    subject = serializers.StringRelatedField(source='freelancer.subject', many=True)
    location = serializers.CharField(source='freelancer.country', read_only=True)
    about = serializers.CharField(source='freelancer.about', read_only=True)
    bio = serializers.CharField(source='freelancer.bio', read_only=True)
    timezone = serializers.CharField(source='freelancer.timezone', read_only=True)
    files = UploadFileSerializer(many=True, read_only=True)
     
    class Meta:
        model = Proposal
        fields = ['id','freelancer', 'freelancer_username','about', 'subject', 'language', 'assignment_type',  'service_type',
                   'bio', 'freelancer_profile_image', 'job_title', 'cover_letter',
                   'files', 'bid_amount', 'submitted_at', 'attachment', 'viewed', 'viewed_at', 'skills', 
                   'expertise', 'location', 'timezone', 'accepted', 'declined']

    def get_submitted_at(self, obj):
        return self.format_time(obj.submitted_at)

    def get_viewed_at(self, obj):
        if obj.viewed_at:
            return self.format_time(obj.viewed_at)
        return None

    def format_time(self, time):
        now = timezone.now()
        delta = now - time
        if delta.days > 0:
            return f"{delta.days} {'day' if delta.days == 1 else 'days'} ago"
        elif delta.seconds // 3600 > 0:
            return f"{delta.seconds // 3600} {'hour' if delta.seconds // 3600 == 1 else 'hours'} ago"
        elif delta.seconds // 60 > 0:
            return f"{delta.seconds // 60} {'minute' if delta.seconds // 60 == 1 else 'minutes'} ago"
        else:
            return "Just now"


class JobSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    remaining_time = serializers.SerializerMethodField()
    order_id = serializers.SerializerMethodField()  # Add SerializerMethodField for order_id
    client = serializers.StringRelatedField(source='client.work_email', read_only=True)
    skills = serializers.StringRelatedField(many=True)
    style = serializers.StringRelatedField(many=True)
    subjects = serializers.StringRelatedField(many=True)
    assignment_types = serializers.StringRelatedField(many=True)
    service_type = serializers.StringRelatedField(many=True)
    languages = serializers.StringRelatedField(many=True)
    levels = serializers.StringRelatedField(many=True)
    education_levels = serializers.StringRelatedField(many=True)
    expertise = serializers.StringRelatedField(many=True)
    files = UploadFileSerializer(many=True, read_only=True)

    class Meta:
        model = Job
        fields = '__all__'

    def get_created_at(self, obj):
        now = timezone.now()
        delta = now - obj.created_at
        if delta.days > 0:
            return f"{delta.days} {'day' if delta.days == 1 else 'days'} ago"
        elif delta.seconds // 3600 > 0:
            return f"{delta.seconds // 3600} {'hour' if delta.seconds // 3600 == 1 else 'hours'} ago"
        elif delta.seconds // 60 > 0:
            return f"{delta.seconds // 60} {'minute' if delta.seconds // 60 == 1 else 'minutes'} ago"
        else:
            return "Just now"
    
    def get_remaining_time(self, obj):
        now = timezone.now()
        due_date_end = datetime.combine(obj.due_date, time.max)
        due_date_end = timezone.make_aware(due_date_end, timezone.get_default_timezone())
        delta = due_date_end - now

        if delta.days == 0:
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            if hours > 0:
                return f"{hours} {'hour' if hours == 1 else 'hours'}, {minutes} {'minute' if minutes == 1 else 'minutes'}"
            else:
                return f"{minutes} {'minute' if minutes == 1 else 'minutes'}"
        elif delta.days < 0:
            return "Date Passed"
        else:
            return f"{delta.days + 1} {'day' if delta.days + 1 == 1 else 'days'}"

    def get_order_id(self, obj):
        # Check if there is a HiredFreelancer associated with this job that has started
        try:
            hired_freelancer = HiredFreelancer.objects.get(job=obj, started=True)
            return hired_freelancer.order_id
        except HiredFreelancer.DoesNotExist:
            return None
class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name']




class JobSubmissionSerializer(serializers.ModelSerializer):
    files = UploadFileSerializer(many=True, read_only=True)
    job = serializers.PrimaryKeyRelatedField(read_only=True)
    freelancer = serializers.StringRelatedField(read_only=True)
    submitted_at = serializers.SerializerMethodField()

    class Meta:
        model = JobSubmission
        fields = ['id', 'job', 'freelancer', 'files', 'satisfied', 'need_revision', 'submitted_at', 'submission_notes']
    
    def get_submitted_at(self, instance):
        return self.format_time(instance.submitted_at)

    
    def format_time(self, time):
        now = timezone.now()
        delta = now - time
        if delta.days > 0:
            return f"{delta.days} {'day' if delta.days == 1 else 'days'} ago"
        elif delta.seconds // 3600 > 0:
            return f"{delta.seconds // 3600} {'hour' if delta.seconds // 3600 == 1 else 'hours'} ago"
        elif delta.seconds // 60 > 0:
            return f"{delta.seconds // 60} {'minute' if delta.seconds // 60 == 1 else 'minutes'} ago"
        else:
            return "Just now"


    
class RevisionSerializer(serializers.ModelSerializer):
    files = UploadFileSerializer(many=True, read_only=True)
    job = serializers.PrimaryKeyRelatedField(read_only=True)
    freelancer = serializers.StringRelatedField(read_only=True)
    submitted_at = serializers.SerializerMethodField()

    class Meta:
        model = Revision
        fields = ['id', 'job', 'freelancer', 'files', 'submission_notes', 'submitted_at']
    
    def get_submitted_at(self, instance):
        return self.format_time(instance.submitted_at)

    
    def format_time(self, time):
        now = timezone.now()
        delta = now - time
        if delta.days > 0:
            return f"{delta.days} {'day' if delta.days == 1 else 'days'} ago"
        elif delta.seconds // 3600 > 0:
            return f"{delta.seconds // 3600} {'hour' if delta.seconds // 3600 == 1 else 'hours'} ago"
        elif delta.seconds // 60 > 0:
            return f"{delta.seconds // 60} {'minute' if delta.seconds // 60 == 1 else 'minutes'} ago"
        else:
            return "Just now"

class JobStatus(serializers.ModelSerializer):
    started_at = serializers.SerializerMethodField()
    finished_at = serializers.SerializerMethodField()

    class Meta:
        model = HiredFreelancer
        fields = ['id', 'job', 'started_at', 'freelancer',
                   'finished_at', 'pending', 'started', 'completed']
        read_only_fields = ['job']

    def get_started_at(self, obj):
        if obj.started:
            return self.format_time(obj.started_at)
        else:
            return "Not started"

    def get_finished_at(self, obj):
        if obj.completed and obj.finished_at:
            return self.format_time(obj.finished_at)
        else:
            return "On progress"
        
    def format_time(self, time):
        now = timezone.now()
        delta = now - time
        if delta.days > 0:
            return f"{delta.days} {'day' if delta.days == 1 else 'days'} ago"
        elif delta.seconds // 3600 > 0:
            return f"{delta.seconds // 3600} {'hour' if delta.seconds // 3600 == 1 else 'hours'} ago"
        elif delta.seconds // 60 > 0:
            return f"{delta.seconds // 60} {'minute' if delta.seconds // 60 == 1 else 'minutes'} ago"
        else:
            return "Just now"
        
class RevisionReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = RevisionReason
        fields = ['id', 'job', 'reason', 'created_at']

