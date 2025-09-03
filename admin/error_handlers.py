from django.shortcuts import render
from django.http import HttpResponseBadRequest, HttpResponseServerError


def custom_400_view(request, exception=None):
    """
    Custom 400 Bad Request error handler.
    """
    return HttpResponseBadRequest(
        render(request, '400.html', status=400)
    )


def custom_500_view(request):
    """
    Custom 500 Internal Server Error handler.
    """
    return HttpResponseServerError(
        render(request, '500.html', status=500)
    )