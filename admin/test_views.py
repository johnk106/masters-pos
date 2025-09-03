from django.http import HttpResponseBadRequest, HttpResponseServerError
from django.shortcuts import render


def test_400_error(request):
    """
    Test view to trigger a 400 error.
    """
    raise Exception("Test 400 error")


def test_500_error(request):
    """
    Test view to trigger a 500 error.
    """
    # This will cause a 500 error
    result = 1 / 0
    return render(request, 'landing/homepage.html')