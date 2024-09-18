from rest_framework import serializers
from api.models import (
    Freelancer, Expertise, Skill, Portfolio, Job, Client, Level, Proposal, HiredFreelancer, Education, EducationlLevel,
      DeclinedJob, JobSubmission, UploadFile, Revision, RevisionReason, Language, AssignmentType, Subject, ServiceType)
from datetime import datetime , timedelta, time
from django.utils import timezone
from django.template.defaultfilters import date as _date
from django.contrib.humanize.templatetags.humanize import naturaltime

class UploadFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadFile
        fields = ['id', 'file', 'uploaded_at']

class AfterRegisterSerializer(serializers.ModelSerializer):
    class Meta: 
        model = Freelancer
        fields = ['expertise', 'skills', 'experience_years', 'short_skills_description','language','service_type', 'subject','assignment_type', 'about',
            'bio']

    

class UpdateVerificationCredentialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Freelancer
        fields = [
            'national_id_front',
            'national_id_back',
            'driving_license_front',
            'passport_front',
            'selfie_image',
            'certificate',
            'proof_of_residence',
        ]

class FreelancerProfileSerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    updated_at = serializers.SerializerMethodField()
    expertise = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    subject = serializers.SerializerMethodField()
    language = serializers.SerializerMethodField()
    assignment_type = serializers.SerializerMethodField()
    service_type = serializers.SerializerMethodField()

    class Meta:
        model = Freelancer
        fields = [
            'id',
            'timezone', 
            'county', 
            'service_type',
            'subject',
            'assignment_type',
            'language',
            'city', 
            'country',
            'first_name',
            'last_name',
            'username',
            'profile_image',
            'receive_news_option',
            'work_email',
            'is_active',
            'email_verified',
            'expertise',
            'skills',
            'about',
            'bio',
            'short_skills_description',
            'experience_years',
            'national_id_front',
            'national_id_back',
            'driving_license_front',
            'passport_front',
            'selfie_image',
            'certificate',
            'proof_of_residence',
            'verified',
            'created_at',
            'updated_at',
        ]

    def get_created_at(self, obj):
        return self.format_datetime(obj.created_at)

    def get_updated_at(self, obj):
        return self.format_datetime(obj.updated_at)

    def format_datetime(self, datetime_field):
        formatted_date = datetime_field.strftime("%B %d, %Y")
        formatted_time = datetime_field.strftime("%I:%M %p")
        return f"{formatted_date} at {formatted_time}"

    def get_expertise(self, obj):
        if isinstance(self.instance, Freelancer):
            expertise_ids = self.instance.expertise.values_list('id', flat=True)
            expertise_data = Expertise.objects.filter(id__in=expertise_ids).values('id', 'expertise')
            return expertise_data
        return []

    def get_skills(self, obj):
        if isinstance(self.instance, Freelancer):
            skill_ids = self.instance.skills.values_list('id', flat=True)
            skill_data = Skill.objects.filter(id__in=skill_ids).values('id', 'name')
            return skill_data
        return []
    
    def get_language(self, obj):
        if isinstance(self.instance, Freelancer):
            languages_ids = self.instance.language.values_list('id', flat=True)
            language_data = Language.objects.filter(id__in=languages_ids).values('id', 'name')
            return language_data
        return []
    
    def get_subject(self, obj):
        if isinstance(self.instance, Freelancer):
            subject_ids = self.instance.subject.values_list('id', flat=True)
            subject_data = Subject.objects.filter(id__in=subject_ids).values('id', 'name')
            return subject_data
        return []
    
    def get_service_type(self, obj):
        if isinstance(self.instance, Freelancer):
            service_ids = self.instance.service_type.values_list('id', flat=True)
            service_data = ServiceType.objects.filter(id__in=service_ids).values('id', 'name')
            return service_data
        return []
    
    def get_assignment_type(self, obj):
        if isinstance(self.instance, Freelancer):
            type_ids = self.instance.assignment_type.values_list('id', flat=True)
            type_data = AssignmentType.objects.filter(id__in=type_ids).values('id', 'name')
            return type_data
        return []

class PortfolioSerializer(serializers.ModelSerializer):
    freelancer = serializers.StringRelatedField(source='freelancer.work_email', read_only=True)
    
    class Meta:
        model = Portfolio
        fields = ['id', 'freelancer', 'title', 'description', 'image', 'document', 'link']
        extra_kwargs = {
            'image': {'required': False},   # Set image field as optional
            'document': {'required': False} # Set document field as optional
        }

    def validate(self, attrs):
        # Custom validation for files
        if not attrs.get('image') and not attrs.get('document'):
            raise serializers.ValidationError("Either an image or a document must be provided.")
        return attrs

class EducationLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationlLevel
        fields = ['id', 'name']
        
        
class EducationFetchSerializer(serializers.ModelSerializer):
    freelancer = serializers.StringRelatedField(source='freelancer.work_email', read_only=True)
    education_levels = EducationLevelSerializer(many=True)  # Use the EducationLevelSerializer here

    class Meta:
        model = Education
        fields = ['id', 'freelancer', 'graduated_from', 'academic_major', 'certificate', 'education_levels']

    def create(self, validated_data):
        education_level_data = validated_data.pop('education_levels', [])

        # Create the education instance
        education = Education.objects.create(**validated_data)
        
        # Set the many-to-many field
        education.education_levels.set(education_level_data)

        # Save certificate if present
        certificate = validated_data.get('certificate', None)
        if certificate:
            education.certificate = certificate
            education.save()

        return education


class EducationSerializer(serializers.ModelSerializer):
    freelancer = serializers.StringRelatedField(source='freelancer.work_email', read_only=True)
    education_levels = serializers.PrimaryKeyRelatedField(queryset=EducationlLevel.objects.all(), many=True)

    class Meta:
        model = Education
        fields = ['id', 'freelancer', 'graduated_from', 'academic_major', 'certificate', 'education_levels']

    def create(self, validated_data):
        education_level_data = validated_data.pop('education_levels', [])

        # Create the education instance
        education = Education.objects.create(**validated_data)
        
        # Set the many-to-many field
        education.education_levels.set(education_level_data)

        # Save certificate if present
        certificate = validated_data.get('certificate', None)
        if certificate:
            education.certificate = certificate
            education.save()

        return education




class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'

class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Level
        fields = '__all__'

class ExpertiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expertise
        fields = '__all__'

class UploadFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadFile
        fields = ['id', 'file', 'uploaded_at']

class AllJobsSerializer(serializers.ModelSerializer):
    time_posted = serializers.SerializerMethodField()
    client_username = serializers.CharField(source='client.username', read_only=True)
    client_location = serializers.CharField(source='client.country', read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    expertise = ExpertiseSerializer(many=True, read_only=True)
    remaining_time = serializers.SerializerMethodField()  # New field for remaining time
    files = UploadFileSerializer(many=True, read_only=True)
    client_join_date = serializers.SerializerMethodField()
    client_jobs_count = serializers.SerializerMethodField()
    style = serializers.StringRelatedField(many=True)
    subjects = serializers.StringRelatedField(many=True)
    assignment_types = serializers.StringRelatedField(many=True)
    service_type = serializers.StringRelatedField(many=True)
    languages = serializers.StringRelatedField(many=True)
    levels = serializers.StringRelatedField(many=True)
    education_levels = serializers.StringRelatedField(many=True)
 
    class Meta:
        model = Job
        fields = '__all__'

    def get_client_join_date(self, obj):
        # Retrieve the client's join date
        return obj.client.date_joined.strftime("%Y-%m-%d")
    
    def get_client_jobs_count(self, obj):
        # Retrieve the count of jobs posted by the client
        return Job.objects.filter(client=obj.client).count()

    def get_time_posted(self, obj): 
        return naturaltime(obj.created_at)
        
    def get_remaining_time(self, obj):
        # Get the current time as timezone-aware datetime
        now = timezone.now()
        
        # Convert the due_date (date object) to a datetime at the end of the day (23:59:59)
        due_date_end = datetime.combine(obj.due_date, time.max)
        due_date_end = timezone.make_aware(due_date_end, timezone.get_default_timezone())
        
        # Calculate the difference
        delta = due_date_end - now

        if delta.days == 0:  # Less than 24 hours remaining
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            
            if hours > 0:
                return f"{hours} {'hour' if hours == 1 else 'hours'}, {minutes} {'minute' if minutes == 1 else 'minutes'}"
            else:
                return f"{minutes} {'minute' if minutes == 1 else 'minutes'}"
        elif delta.days < 0:  # Due date has passed
            return "Date Passed"
        else:
            # If more than one day is remaining
            return f"{delta.days + 1} {'day' if delta.days + 1 == 1 else 'days'}"

class MatchingJobsSerializer(serializers.ModelSerializer):
    time_posted = serializers.SerializerMethodField()
    client_username = serializers.CharField(source='client.username', read_only=True)
    client_location = serializers.CharField(source='client.country', read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    expertise = ExpertiseSerializer(many=True, read_only=True)
    remaining_time = serializers.SerializerMethodField() 

    class Meta:
        model = Job
        fields = '__all__'
        ordering = ['-created_at']

    def get_time_posted(self, obj): 
        return naturaltime(obj.created_at)
    
    def get_remaining_time(self, obj):
        now = timezone.now()  # Use timezone-aware datetime
        due_date_time = datetime.combine(obj.due_date, datetime.max.time())
        due_date_time = timezone.make_aware(due_date_time, timezone.get_default_timezone())
        delta = due_date_time - now

        if delta.days > 0:
            # If more than one day is remaining
            return f"{delta.days} {'day' if delta.days == 1 else 'days'}"
        elif delta.total_seconds() > 0:
            # Less than one day remaining, calculate hours, minutes, and seconds
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            seconds = delta.seconds % 60
            
            # Conditionally format string based on what components are greater than zero
            time_parts = []
            if hours > 0:
                time_parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
            if minutes > 0:
                time_parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}")
            if seconds > 0:
                time_parts.append(f"{seconds} {'second' if seconds == 1 else 'seconds'}")
            
            return ", ".join(time_parts) if time_parts else "Due momentarily"
        else:
            return "Date Passed"

class ProposalSerializer(serializers.ModelSerializer):
    submitted_at = serializers.SerializerMethodField()
    viewed_at = serializers.SerializerMethodField()
    files = UploadFileSerializer(many=True, read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_description = serializers.CharField(source='job.description', read_only=True)
    job_skills = serializers.StringRelatedField(source='job.skills', many=True, read_only=True)
    job_expertise = serializers.StringRelatedField(source='job.expertise', many=True, read_only=True)
    job_amount_posted = serializers.DecimalField(source='job.project_cost', max_digits=10, decimal_places=2, read_only=True)
    client_name = serializers.CharField(source='job.client.username', read_only=True)
    client_country = serializers.CharField(source='job.client.country', read_only=True)
    job_time_posted = serializers.CharField(source='job.time_posted', read_only=True)
    job_paid = serializers.BooleanField(source='job.paid', read_only=True)  

    class Meta:
        model = Proposal
        fields = [
            'id', 'job', 'job_title', 'job_description', 'job_skills', 'job_expertise', 
            'job_amount_posted', 'client_name', 'client_country', 'job_time_posted', 
            'job_paid', 'submitted_at', 'cover_letter', 'bid_amount', 'files', 
            'viewed', 'viewed_at', 'accepted', 'declined'
        ]
        read_only_fields = ['job']

    def create(self, validated_data):
        files_data = self.context['request'].FILES
        proposal = Proposal.objects.create(**validated_data)

        for file_data in files_data.getlist('files'):
            upload_file = UploadFile.objects.create(file=file_data)
            proposal.files.add(upload_file)
        return proposal

    
    def get_submitted_at(self, obj): 
        return naturaltime(obj.submitted_at)
    
    def get_viewed_at(self, obj): 
        if obj.viewed_at:
            return naturaltime(obj.viewed_at)
        return None

    
    def format_time(self, time_obj): 
        now = timezone.now()
        delta = now - time_obj
        if delta.days > 0:
            return f"{delta.days} {'day' if delta.days == 1 else 'days'} ago"
        elif delta.seconds // 3600 > 0:
            return f"{delta.seconds // 3600} {'hour' if delta.seconds // 3600 == 1 else 'hours'} ago"
        elif delta.seconds // 60 > 0:
            return f"{delta.seconds // 60} {'minute' if delta.seconds // 60 == 1 else 'minutes'} ago"
        else:
            return "Just now"

class DeclinedJobSerializer(serializers.ModelSerializer):
    freelancer = serializers.PrimaryKeyRelatedField(read_only=True)
    proposal = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = DeclinedJob
        fields = ['freelancer', 'proposal', 'reason', 'declined_at']

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadFile
        fields = ['id', 'file', 'uploaded_at']  # Include any other fields you need


class HiredFreelancerSerializer(serializers.ModelSerializer):
    started_at = serializers.SerializerMethodField()
    finished_at = serializers.SerializerMethodField()
    due_date = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True)
    project_price = serializers.DecimalField(source='job.project_cost', max_digits=10, decimal_places=2, read_only=True)
    client_name = serializers.CharField(source='job.client.username', read_only=True)
    client_id = serializers.UUIDField(source='job.client.id', read_only=True)  # Added field to retrieve client's ID
    num_pages = serializers.IntegerField(source='job.num_pages', read_only=True)
    description = serializers.CharField(source='job.description', read_only=True)
    skills = serializers.StringRelatedField(many=True, source='job.skills')
    expertise = serializers.StringRelatedField(many=True, source='job.expertise')
    level = serializers.CharField(source='job.level', read_only=True)
    assignment_type = serializers.CharField(source='job.assignment_type', read_only=True)
    service = serializers.CharField(source='job.service', read_only=True)
    education_level = serializers.CharField(source='job.education_level', read_only=True)
    language = serializers.CharField(source='job.language', read_only=True)
    assignment_topic = serializers.CharField(source='job.assignment_topic', read_only=True)
    subject = serializers.CharField(source='job.subject', read_only=True)
    citation_style = serializers.CharField(source='job.citation_style', read_only=True)
    remaining_time = serializers.SerializerMethodField()
    files = FileSerializer(many=True, source='job.files')

    style = serializers.StringRelatedField(many=True, source='job.style')
    subjects = serializers.StringRelatedField(many=True, source='job.subjects')
    assignment_types = serializers.StringRelatedField(many=True, source='job.assignment_types')
    service_type = serializers.StringRelatedField(many=True, source='job.service_type')
    languages = serializers.StringRelatedField(many=True, source='job.languages')
    levels = serializers.StringRelatedField(many=True, source='job.levels')
    education_levels = serializers.StringRelatedField(many=True, source='job.education_levels') 

    class Meta:
        model = HiredFreelancer
        fields = ['id', 'job','order_id', 'style', 'subjects', 'assignment_types', 'service_type', 'languages', 'levels',
                  'education_levels', 'job_title', 'project_price', 'client_name', 'client_id',
                   'num_pages', 'description', 'skills', 'expertise', 'level', 
                   'assignment_type', 'service', 'education_level', 'language', 
                   'assignment_topic', 'subject', 'citation_style', 'started_at', 
                   'finished_at', 'pending', 'revisions', 'started', 'completed',
                     'due_date', 'remaining_time','files']
        read_only_fields = ['job']

    def get_files(self, obj):
        files = obj.job.files.all()  # Assuming you have a related_name 'files' for the M2M field
        serializer = FileSerializer(instance=files, many=True)
        return serializer.data

    def get_started_at(self, obj):
        if obj.started:
            return self.format_date(obj.started_at)
        else:
            return "Not started"

    def get_finished_at(self, obj):
        if obj.completed and obj.finished_at:
            return self.format_date(obj.finished_at)
        else:
            return "In progress"
    def format_date(self, time):
        return time.strftime("%B %d, %Y")
        
    def get_due_date(self, obj):
        job = obj.job
        return job.due_date.strftime("%Y-%m-%d") if job.due_date else "No due date"

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
    
    def get_remaining_time(self, obj):
        now = timezone.now()
        due_date_time = datetime.combine(obj.job.due_date, time.max)
        due_date_time = timezone.make_aware(due_date_time, timezone.get_default_timezone())
        delta = due_date_time - now

        if delta.days > 0:
            return f"{delta.days} {'day' if delta.days == 1 else 'days'}"
        elif delta.total_seconds() > 0:
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            return f"{hours} {'hour' if hours == 1 else 'hours'}, {minutes} {'minute' if minutes == 1 else 'minutes'}"
        else:
            return "Date Passed"
     
class JobSubmissionSerializer(serializers.ModelSerializer):
    files = UploadFileSerializer(many=True, read_only=True)
    job = serializers.PrimaryKeyRelatedField(read_only=True)
    freelancer = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = JobSubmission
        fields = ['id', 'job', 'freelancer', 'files', 'satisfied', 'need_revision', 'submitted_at', 'submission_notes']

    def create(self, validated_data):
        files_data = self.context['request'].FILES
        job_submission = JobSubmission.objects.create(
            job=validated_data['job'],
            freelancer=validated_data['freelancer'],
            submission_notes=validated_data.get('submission_notes', '')
        )

        # Upload files and add to the job_submission.files ManyToMany field
        for file_data in files_data.getlist('files'):
            upload_file = UploadFile.objects.create(file=file_data)
            job_submission.files.add(upload_file)  # Add file to the ManyToMany field

        job_submission.save()  # Save the job_submission to update the ManyToMany relationship
        return job_submission

    
class RevisionSerializer(serializers.ModelSerializer):
    files = UploadFileSerializer(many=True, read_only=True)
    job = serializers.PrimaryKeyRelatedField(read_only=True)
    freelancer = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Revision
        fields = ['id', 'job', 'freelancer', 'files', 'submission_notes', 'submitted_at']

    def create(self, validated_data):
        files_data = self.context['request'].FILES
        revision_submission = Revision.objects.create(
            job=validated_data['job'],
            freelancer=validated_data['freelancer'],
            submission_notes=validated_data.get('submission_notes', '')
        )
        for file_data in files_data.getlist('files'):
            upload_file = UploadFile.objects.create(file=file_data)
            revision_submission.files.add(upload_file)  # Add file to the ManyToMany field

        revision_submission.save()  # Save the job_submission to update the ManyToMany relationship
        return revision_submission
    
class RevisionReasonSerializer(serializers.ModelSerializer):
    job = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = RevisionReason
        fields = ['id', 'job', 'reason', 'created_at']



