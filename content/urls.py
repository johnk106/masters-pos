from django.urls import path
from . import views


app_name='content'
urlpatterns = [
    path('faqs/',views.faqs,name='faqs')
]