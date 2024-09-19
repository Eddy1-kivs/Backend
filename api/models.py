import uuid
from django.db import models
import bcrypt
from django.contrib.auth.models import AbstractUser, BaseUserManager, Group, Permission
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import random  
from dirtyfields import DirtyFieldsMixin 
from django.utils.crypto import get_random_string

class Skill(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Subject(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class AssignmentType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class ServiceType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class Language(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Style(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Level(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class LineSpacing(models.Model):
    name = models.CharField(max_length=255)
 
    def __str__(self):
        return self.name
    
class EducationlLevel(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

class Expertise(models.Model):
    
    expertise = models.CharField(max_length=255)

    def __str__(self):
        return self.expertise


class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)  # Add created_at field
    updated_at = models.DateTimeField(auto_now=True)  # Add updated_at field
    # password = models.CharField(max_length=128)
    profile_image = models.ImageField(
        upload_to='profile_images/', default='profile_images/default.svg.png',  blank=True, null=True)
    otp_code = models.CharField( 
        max_length=6, null=True, blank=True)
    county = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    timezone = models.CharField(max_length=255, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    country = models.CharField(max_length=255)
    receive_news_option = models.BooleanField(default=False)
    client_status = models.BooleanField(default=False)
    freelancer_status = models.BooleanField(default=False)
    suspend = models.BooleanField(default=False)
    CVs = models.FileField(upload_to='CVs', blank=True, null=True)
    stuff_application = models.BooleanField(default=False)
    verified = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',
        blank=True,
        
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    def __str__(self):
        return self.username

    def __str__(self): 
        return self.username
    
    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.generate_unique_username()
        super().save(*args, **kwargs)
    
    def generate_unique_username(self):
        return get_random_string(length=32)



class Freelancer(CustomUser):
    expertise = models.ManyToManyField(Expertise)
    skills = models.ManyToManyField(Skill)
    subject = models.ManyToManyField(Subject)
    assignment_type = models.ManyToManyField(AssignmentType)
    service_type = models.ManyToManyField(ServiceType)
    language = models.ManyToManyField(Language)
    # verified = models.BooleanField(default=False, verbose_name=_("Credentials Verified"))
    about = models.TextField(null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    short_skills_description = models.CharField(max_length=1000, null=True, blank=True)
    experience_years = models.PositiveIntegerField(null=True, blank=True)
    national_id_front = models.ImageField(
        upload_to='identification/national_id/front/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        blank=True, null=True
    )
    national_id_back = models.ImageField(
        upload_to='identification/national_id/back/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        blank=True, null=True
    )
    driving_license_front = models.ImageField(
        upload_to='identification/driving_license/front/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        blank=True, null=True
    )
    passport_front = models.ImageField(
        upload_to='identification/passport/front/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        blank=True, null=True
    )
    selfie_image = models.ImageField(
        upload_to='selfies/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        blank=True, null=True
    )

    # Other identification documents
    certificate = models.FileField(
        upload_to='credentials/certificates/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        blank=True, null=True
    )
    proof_of_residence = models.FileField(
        upload_to='credentials/proof_of_residence/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        blank=True, null=True
    )


    def __str__(self):
        return self.work_email

    class Meta:
        verbose_name = 'Freelancer'
        verbose_name_plural = 'Freelancers'
    
    def save(self, *args, **kwargs):
        # Compress each image if it's present
        if self.national_id_front:
            self.national_id_front = self.compress_image(self.national_id_front)

        if self.national_id_back:
            self.national_id_back = self.compress_image(self.national_id_back)

        if self.driving_license_front:
            self.driving_license_front = self.compress_image(self.driving_license_front)

        if self.passport_front:
            self.passport_front = self.compress_image(self.passport_front)

        if self.selfie_image:
            self.selfie_image = self.compress_image(self.selfie_image)

        super(Freelancer, self).save(*args, **kwargs)

    def compress_image(self, image):
        # Open the uploaded image
        img = Image.open(image)

        # Convert to RGB if it's PNG or has an alpha channel
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # Resize the image to a max width of 1024px (maintain aspect ratio)
        img.thumbnail((1024, 1024))

        # Save the image to a BytesIO object
        img_io = io.BytesIO()
        img.save(img_io, format='JPEG', quality=60)  # Set compression quality to 60
        img_io.seek(0)

        # Create a new InMemoryUploadedFile for the compressed image
        compressed_image = InMemoryUploadedFile(
            img_io,
            'ImageField',
            image.name,
            'image/jpeg',
            sys.getsizeof(img_io),
            None
        )

        return compressed_image

class Client(CustomUser):

    def __str__(self):
        return self.work_email
    
    class Meta:
        verbose_name = 'Client'
        verbose_name_plural = 'Clients'


class Test(models.Model):
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE)
    topic = models.TextField(null=True, blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    file = models.FileField(upload_to='test_submissions/', blank=True, null=True)

    def __str__(self):
        return f"Test for {self.freelancer.work_email} on {self.topic}"


class Suspension(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='suspension')
    suspension_reason = models.TextField()
    suspension_days = models.PositiveIntegerField()
    suspension_end_date = models.DateField()

    def __str__(self):
        return f"Suspension for {self.suspension_days} days for user {self.user.username}"


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    work_email = models.EmailField(unique=True)

    def __str__(self):
        return self.work_email
    
class UploadFile(models.Model):
    file = models.FileField(
        upload_to='uploads/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.file.name} uploaded on {self.uploaded_at}"
    
class Education(models.Model):
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE, related_name='educations')
    graduated_from = models.CharField(max_length=255)
    academic_major = models.CharField(max_length=255)
    education_levels = models.ManyToManyField(EducationlLevel)
    certificate = models.FileField(upload_to='education_certificates/', blank=True, null=True)

    def __str__(self):
        return f"{self.freelancer.work_email}'s Education"
class AmountPerPage(models.Model):
    amount = models.IntegerField()

    def __str__(self):
        return f"Amount Per Page: {self.amount}"


class Job(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    due_date = models.DateField()
    num_pages = models.IntegerField()
    words = models.IntegerField(blank=True, null=True)
    project_cost = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    expertise = models.ManyToManyField(Expertise)
    skills = models.ManyToManyField(Skill) 
    files = models.ManyToManyField(UploadFile, related_name='jobs_files', blank=True)
    assignment_type = models.CharField(max_length=50, null=True, blank=True)
    service = models.CharField(max_length=50, null=True, blank=True)
    language = models.CharField(max_length=100, null=True, blank=True)
    assignment_topic = models.CharField(max_length=255, null=True, blank=True)
    subject = models.CharField(max_length=100, null=True, blank=True)
    citation_style = models.CharField(max_length=100, null=True, blank=True)
    line_spacing = models.ManyToManyField(LineSpacing)
    style = models.ManyToManyField(Style)
    subjects = models.ManyToManyField(Subject)
    assignment_types = models.ManyToManyField(AssignmentType)
    service_type = models.ManyToManyField(ServiceType)
    languages = models.ManyToManyField(Language)
    levels = models.ManyToManyField(Level)
    education_levels = models.ManyToManyField(EducationlLevel)
    page_abstract = models.BooleanField(default=False)
    printable_sources = models.BooleanField(default=False)
    detailed_outline = models.BooleanField(default=False)
    paid = models.BooleanField(default=False) 
    
    def time_posted(self):
        now = timezone.now()
        delta = now - self.created_at
        if delta.days > 0:
            return f"{delta.days} {'day' if delta.days == 1 else 'days'} ago"
        elif delta.seconds // 3600 > 0:
            return f"{delta.seconds // 3600} {'hour' if delta.seconds // 3600 == 1 else 'hours'} ago"
        elif delta.seconds // 60 > 0:
            return f"{delta.seconds // 60} {'minute' if delta.seconds // 60 == 1 else 'minutes'} ago"
        else:
            return "Just now"

    def __str__(self):
        return self.title
    
class Transactions(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="users")
    job = models.OneToOneField('Job', on_delete=models.CASCADE, null=True, blank=True)
    transaction_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=50)  # e.g., 'pending', 'completed', 'failed'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} for {self.user.username}"
    
class Invite(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)
    declined_reason = models.TextField(null=True, blank=True)
    viewed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.viewed and not self.viewed_at:
            self.viewed_at = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invite from {self.client.work_email} to {self.freelancer.work_email} for {self.job.title}"

class Attachment(models.Model):
    job = models.ForeignKey(Job, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='jobs/attachments/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

class Portfolio(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE, related_name='portfolios')
    title = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='portfolio_images/', blank=True, null=True)
    document = models.FileField(upload_to='portfolio_files/', blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title 
    
class Proposal(DirtyFieldsMixin, models.Model):
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    cover_letter = models.TextField()
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2, default='1')
    submitted_at = models.DateTimeField(auto_now_add=True)
    files = models.ManyToManyField(UploadFile, related_name='proposal_files', blank=True)
    viewed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(null=True, blank=True)  
    accepted = models.BooleanField(default=False)
    declined = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Proposal"
        verbose_name_plural = "Proposals"

    def __str__(self):
        return f"Proposal by {self.freelancer.email} for {self.job.title}"

    def save(self, *args, **kwargs):
        if self.viewed and not self.viewed_at:
            self.viewed_at = timezone.now()
        super().save(*args, **kwargs)

class DeclinedJob(models.Model):
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE)
    proposal = models.ForeignKey(Proposal, on_delete=models.CASCADE)
    reason = models.TextField(blank=True, null=True)
    declined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Declined Job"
        verbose_name_plural = "Declined Jobs"

    def __str__(self):
        return f"{self.freelancer} declined job for {self.proposal.job.title}"


class HiredFreelancer(models.Model):
    freelancer = models.ForeignKey(Freelancer, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    pending = models.BooleanField(default=False, verbose_name=_("Pending"))
    revisions = models.BooleanField(default=False, verbose_name=_("Revisions"))
    started = models.BooleanField(default=False, verbose_name=_("Started"))
    completed = models.BooleanField(default=False, verbose_name=_("Completed"))
    order_id = models.IntegerField(null=True, verbose_name=_("Order ID"), editable=False)

    class Meta:
        verbose_name = "Hired Freelancer"
        verbose_name_plural = "Hired Freelancers"

    def __str__(self):
        return f"{self.freelancer.email} hired for {self.job.title}"

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = random.randint(10000000, 99999999)  # Generate random 8-digit number
        if self.completed and not self.finished_at:
            self.finished_at = timezone.now()
        super().save(*args, **kwargs)

class JobSubmission(models.Model):
    job = models.ForeignKey(Job, related_name='submissions', on_delete=models.CASCADE)
    freelancer = models.ForeignKey(Freelancer, related_name='submissions', on_delete=models.CASCADE)
    files = models.ManyToManyField(UploadFile, related_name='submission_files', blank=True)
    satisfied = models.BooleanField(default=False)
    need_revision = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    submission_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.freelancer.work_email} submission for {self.job.title}"

class Revision(models.Model):
    job = models.ForeignKey(Job, related_name='revisions', on_delete=models.CASCADE, blank=True, null=True)
    freelancer = models.ForeignKey(Freelancer, related_name='revisions', on_delete=models.CASCADE, blank=True, null=True)
    files = models.ManyToManyField(UploadFile, related_name='revision_files', blank=True)
    submission_notes = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revision for {self.job.title} by {self.freelancer.work_email}" 


class RevisionReason(models.Model):
    job = models.ForeignKey(Job, related_name='revision_reasons', on_delete=models.CASCADE)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Revision Reason for {self.job.title}"
    
class Messaging(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="user")
    sender = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="sender")
    receiver = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="receiver")
    message = models.CharField(max_length=1000)
    is_read = models.BooleanField(default=False)
    files = models.ManyToManyField(UploadFile, related_name='message_files', blank=True)
    timestamp = models.DateTimeField(auto_now_add=True) 
    
    class Meta:
        ordering = ['timestamp']
        verbose_name_plural = "Message"

    def __str__(self):
        return f"{self.sender} - {self.receiver}"


class Review(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reviewer = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="reviewer")
    recipient = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="recipient")
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=0)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review for {self.job.title} by {self.reviewer.work_email}"


class Card(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='master_cards')
    cardholder_name = models.CharField(max_length=255)
    card_number = models.CharField(max_length=16)
    expiration_date = models.DateField()
    cvv = models.CharField(max_length=4)
    card_type = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.cardholder_name}'s card ending in {self.card_number[-4:]}"



class PayPal(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='paypal_accounts')
    email = models.EmailField()

    def __str__(self):
        return self.email


class Mpesa(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='mpesa_accounts')
    phone_number = models.CharField(max_length=15)

    def __str__(self):
        return self.phone_number

class Wallet(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Wallet for {self.user.work_email}"

    def deposit(self, amount):
        self.balance += amount
        self.save()

    def withdraw(self, amount):
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False

    def transaction_history(self):
        return Transaction.objects.filter(wallet=self).order_by('-timestamp')[:10]

class Transaction(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='transaction')
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    transaction_type = models.CharField(max_length=20)
    method_used = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.transaction_type} of {self.amount} on {self.timestamp}"
    
class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)
    url = models.URLField(null=True, blank=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:20]}..."

