from django.contrib import admin
from .models import (
    CustomUser, Freelancer, Client, Job, Skill, Expertise, Portfolio, Proposal, HiredFreelancer, Messaging, Attachment, Education, DeclinedJob,
    UploadFile, JobSubmission, Revision, RevisionReason, Review, Card, PayPal, Mpesa, Wallet, Transaction, Suspension, AmountPerPage,
    Subject, AssignmentType, Language, ServiceType, Style, Level, EducationlLevel, Test, Notification, LineSpacing, Invite, Transactions
)

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'work_email', 'username', 'first_name', 'last_name', 'country', 'is_active') 

admin.site.register(CustomUser, CustomUserAdmin)

class TransactionsAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'transaction_id', 'amount', 'status')

admin.site.register(Transactions, TransactionsAdmin)

class ClientAdmin(admin.ModelAdmin):
    list_display = ('id', 'work_email', 'username', 'first_name', 'last_name', 'country', 'is_active') 

class FreelancerAdmin(admin.ModelAdmin):
    list_display = ('id', 'work_email', 'username', 'first_name', 'last_name', 'country', 'is_active',
                    'email_verified') 

class JobAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'client', 'due_date')
    filter_horizontal = ('files',)

class SkillAdmin(admin.ModelAdmin):
    list_display = ('name',)

class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name',)

class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)

class LevelAdmin(admin.ModelAdmin):
    list_display = ('name',)

class EducationLevelAdmin(admin.ModelAdmin):
    list_display = ('name',)

class ServiceTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)

class StyleAdmin(admin.ModelAdmin):
    list_display = ('name',)


class AssignmentTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)


class LineSpacingAdmin(admin.ModelAdmin):
    list_display = ('name',)

class ExpertiseAdmin(admin.ModelAdmin):
    list_display = ('expertise',)


class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('title', 'freelancer')

class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('job', 'file')

class InviteAdmin(admin.ModelAdmin):
    list_display = ('job', 'freelancer', 'client', 'sent_at', 'accepted', 'declined')

class ProposalAdmin(admin.ModelAdmin):
    list_display = ('id', 'freelancer', 'job', 'bid_amount', 'submitted_at')

class HiredFreelancerAdmin(admin.ModelAdmin):
    list_display = ('id','order_id', 'freelancer', 'job', 'started_at', 'finished_at', 'pending', 'revisions', 'started', 'completed')

class ChatMessageAdmin(admin.ModelAdmin):
    list_editable = ['is_read', 'message']
    list_display = ['user','sender', 'receiver', 'is_read', 'message']

class EducationAdmin(admin.ModelAdmin):
    list_display = ('freelancer', 'graduated_from', 'academic_major', 'certificate')

class DeclinedJobAdmin(admin.ModelAdmin):
    list_display = ('freelancer', 'proposal', 'reason', 'declined_at')

class UploadFileAdmin(admin.ModelAdmin):
    list_display = ('file', 'uploaded_at')

class JobSubmissionAdmin(admin.ModelAdmin):
    list_display = ('job', 'freelancer', 'satisfied', 'need_revision', 'submitted_at')
    filter_horizontal = ('files',)  # Allows selection of multiple files in admin

class RevisionAdmin(admin.ModelAdmin):
    list_display = ('job', 'freelancer', 'submitted_at')
    filter_horizontal = ('files',)  # Allows selection of multiple files in admin

class RevisionReasonAdmin(admin.ModelAdmin):
    list_display = ('id', 'job', 'reason', 'created_at')

class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'reviewer', 'recipient', 'job', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('reviewer__work_email', 'recipient__work_email', 'job__title')

class CardAdmin(admin.ModelAdmin):
    list_display = ('cardholder_name', 'card_number', 'expiration_date', 'cvv', 'user', 'card_type')

class PayPalAdmin(admin.ModelAdmin):
    list_display = ('email', 'user')

class MpesaAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'user')

class AmountPerPageAdmin(admin.ModelAdmin):
    list_display = ('id', 'amount')

class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')
    search_fields = ('user__work_email',)

class TransactionAdmin(admin.ModelAdmin):
    list_display = ('user', 'wallet', 'amount', 'timestamp', 'transaction_type', 'method_used')
    search_fields = ('wallet__user__work_email',)

class SuspensionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'suspension_reason', 'suspension_days', 'suspension_end_date')

admin.site.register(Suspension, SuspensionAdmin)
admin.site.register(Messaging, ChatMessageAdmin)
admin.site.register(Client, ClientAdmin)
admin.site.register(Freelancer, FreelancerAdmin)
admin.site.register(Job, JobAdmin) 
admin.site.register(Skill, SkillAdmin)
admin.site.register(Expertise, ExpertiseAdmin)
admin.site.register(Portfolio, PortfolioAdmin) 
admin.site.register(Proposal, ProposalAdmin)
admin.site.register(HiredFreelancer, HiredFreelancerAdmin)
admin.site.register(Attachment, AttachmentAdmin) 
admin.site.register(Education, EducationAdmin) 
admin.site.register(DeclinedJob, DeclinedJobAdmin)
admin.site.register(UploadFile, UploadFileAdmin)
admin.site.register(JobSubmission, JobSubmissionAdmin)
admin.site.register(Revision, RevisionAdmin)
admin.site.register(RevisionReason, RevisionReasonAdmin)
admin.site.register(Review, ReviewAdmin)
admin.site.register(Card, CardAdmin)
admin.site.register(PayPal, PayPalAdmin)
admin.site.register(Mpesa, MpesaAdmin)
admin.site.register(Wallet, WalletAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(AmountPerPage, AmountPerPageAdmin)
admin.site.register(Language, LanguageAdmin)
admin.site.register(Style, StyleAdmin)
admin.site.register(ServiceType, ServiceTypeAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(AssignmentType, AssignmentTypeAdmin)
admin.site.register(Level, LevelAdmin) 
admin.site.register(EducationlLevel, EducationLevelAdmin)
admin.site.register(Test)
admin.site.register(LineSpacing, LineSpacingAdmin)
admin.site.register(Notification) 
admin.site.register(Invite, InviteAdmin)
