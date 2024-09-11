from django.shortcuts import render

# View to render the signup page
def home(request):
    return render(request, 'signup_with_google.html')

# View to handle post-signup redirection
def signup_success_view(request):
    return render(request, 'signup_success.html')

from allauth.socialaccount.models import SocialApp

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from allauth.socialaccount.models import SocialApp

# View to render the social applications information
@staff_member_required
def show_social_applications(request):
    social_apps = SocialApp.objects.all()
    context = {'social_apps': social_apps}
    return render(request, 'social_apps_info.html', context)
