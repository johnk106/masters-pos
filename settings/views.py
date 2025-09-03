from django.shortcuts import render
from django.contrib.auth.decorators import login_required
@login_required

# Create your views here.
def profile_settings(request):
    return render(request,'settings/profile-settings.html',{})
@login_required

def security_settings(request):
    return render(request,'settings/security-settings.html',{})

