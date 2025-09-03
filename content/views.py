from django.shortcuts import render

# Create your views here.
def faqs(request):
    return render(request,'content/faqs.html',{})