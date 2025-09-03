from django.core.management.base import BaseCommand
import os
import logging

from sales.services.notification import send_ngrok_link_notification

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send ngrok public URL notification email to configured recipients.'

    def add_arguments(self, parser):
        parser.add_argument('--url', type=str, help='Ngrok public URL; falls back to NGROK_PUBLIC_URL env')

    def handle(self, *args, **options):
        ngrok_url = options.get('url') or os.getenv('NGROK_PUBLIC_URL')
        if not ngrok_url:
            self.stderr.write(self.style.ERROR('NGROK public URL not provided. Use --url or set NGROK_PUBLIC_URL env.'))
            return 1

        ok = send_ngrok_link_notification(ngrok_url)
        if ok:
            self.stdout.write(self.style.SUCCESS('Ngrok notification processed.'))
            return 0
        else:
            self.stderr.write(self.style.ERROR('Ngrok notification failed.'))
            return 2