# authentication/middleware.py

from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
import re

class LoginRequiredMiddleware:
    """
    Middleware that requires a user to be authenticated for all views except:
      - settings.LOGIN_URL (a literal path)
      - settings.LOGOUT_URL (if defined, also a literal path)
      - any named URL in settings.LOGIN_EXEMPT_URLS (reverse()-ed at startup)
      - static/media paths (if added here)
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # 1) Treat LOGIN_URL and LOGOUT_URL as literal paths
        login_path = settings.LOGIN_URL  # e.g. '/dashboard/authentication/accounts/login/'
        logout_path = getattr(settings, 'LOGOUT_URL', None)

        exempt = {login_path}
        if logout_path:
            exempt.add(logout_path)

        # 2) Add any named views from LOGIN_EXEMPT_URLS by reversing them
        for name in getattr(settings, 'LOGIN_EXEMPT_URLS', []):
            try:
                url = reverse(name)
                exempt.add(url)
            except Exception:
                # If reverse(name) fails, skip it
                pass

        # 3) Add static/media prefixes (if you want them exempt)
        static_url = getattr(settings, 'STATIC_URL', None)
        media_url = getattr(settings, 'MEDIA_URL', None)
        if static_url:
            exempt.add(static_url)
        if media_url:
            exempt.add(media_url)

        # Compile regexes for prefix matches
        self.exempt_prefixes = []
        for path in exempt:
            if path.endswith('/'):
                self.exempt_prefixes.append(re.compile(r'^' + re.escape(path)))
            else:
                self.exempt_prefixes.append(re.compile(r'^' + re.escape(path) + r'$'))

        self.exempt = exempt

    def __call__(self, request):
        path = request.path_info

        # If path matches any exempt prefix, allow through
        for regex in self.exempt_prefixes:
            if regex.match(path):
                return self.get_response(request)

        # Otherwise, if user is not authenticated, add message and redirect
        if not request.user.is_authenticated:
            messages.info(request, "Please log in to continue.")
            return redirect(f"{settings.LOGIN_URL}?next={path}")

        # Authenticated → proceed normally
        return self.get_response(request)
