import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "admin.settings")
django_app = get_wsgi_application()
application = WhiteNoise(
    django_app,
    root=os.path.join(os.path.dirname(__file__), "staticfiles"),
    prefix="static/",
)