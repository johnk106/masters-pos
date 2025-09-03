import os
import socket
import time
import logging
from typing import List

from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMultiAlternatives, get_connection
from django.utils import timezone

logger = logging.getLogger(__name__)


def _parse_recipients_from_env() -> List[str]:
    raw = os.getenv('NGROK_NOTIFY_EMAILS', '')
    if not raw:
        return []
    return [email.strip() for email in raw.split(',') if email.strip()]


def _format_subject() -> str:
    return os.getenv('NGROK_NOTIFY_SUBJECT', 'POS is up — ngrok URL')


def _format_bodies(ngrok_url: str) -> tuple[str, str]:
    now_str = timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')
    hostname = socket.gethostname()

    plain = (
        "Your POS is available remotely:\n\n"
        f"{ngrok_url}\n\n"
        f"Started at: {now_str}\n"
        "Host: " + hostname + "\n"
        "Note: ngrok tunnels are ephemeral. Keep this URL private.\n"
        "Do not commit it into code. Access via the links above while the tunnel is active.\n"
    )

    html = (
        "<p>Your POS is available remotely:</p>"
        f"<p><a href=\"{ngrok_url}\">{ngrok_url}</a></p>"
        f"<p>Started at: <strong>{now_str}</strong><br/>"
        f"Host: <code>{hostname}</code></p>"
        "<p><em>Note: ngrok tunnels are ephemeral. Keep this URL private.</em></p>"
        "<p>Do not commit it into code. Access via the links above while the tunnel is active.</p>"
    )

    return plain, html


def _should_send_now(ngrok_url: str, window_seconds: int = 600) -> bool:
    cache_key = f"ngrok_notify_sent:{ngrok_url}"
    last_mark = cache.get(cache_key)
    if last_mark:
        return False
    return True


def _mark_sent(ngrok_url: str, window_seconds: int = 600) -> None:
    cache_key = f"ngrok_notify_sent:{ngrok_url}"
    cache.set(cache_key, True, timeout=window_seconds)


def send_ngrok_link_notification(ngrok_url: str) -> bool:
    """
    Sends an email with the ngrok public URL to recipients from env.

    Respects:
    - NGROK_NOTIFY_ENABLED
    - NGROK_NOTIFY_EMAILS
    - NGROK_NOTIFY_SUBJECT
    - NGROK_NOTIFY_SEND_RETRIES

    Returns True if successfully sent (or skipped due to disabled/config), False if definitively failed.
    """
    try:
        enabled = os.getenv('NGROK_NOTIFY_ENABLED', 'True') == 'True'
        if not enabled:
            logger.info('Ngrok notify: disabled by NGROK_NOTIFY_ENABLED')
            return True

        recipients = _parse_recipients_from_env()
        if not recipients:
            logger.info('Ngrok notify: no recipients configured in NGROK_NOTIFY_EMAILS')
            return True

        # Idempotency window (10 minutes)
        if not _should_send_now(ngrok_url):
            logger.info('Ngrok notify: skipped duplicate send within the idempotency window')
            return True

        subject = _format_subject()
        text_body, html_body = _format_bodies(ngrok_url)

        from_email = settings.DEFAULT_FROM_EMAIL

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=from_email,
            to=recipients,
        )
        message.attach_alternative(html_body, "text/html")

        retries = int(os.getenv('NGROK_NOTIFY_SEND_RETRIES', '3'))
        attempt = 0
        backoff_seconds = 1

        with get_connection() as connection:
            while True:
                try:
                    message.send(fail_silently=False)
                    _mark_sent(ngrok_url)
                    logger.info(
                        "Ngrok notify: email sent",
                        extra={"recipients": recipients, "url": ngrok_url, "time": timezone.now().isoformat()},
                    )
                    return True
                except Exception as send_error:
                    attempt += 1
                    if attempt > retries:
                        logger.error(
                            "Ngrok notify: failed to send after retries",
                            extra={"recipients": recipients, "url": ngrok_url, "time": timezone.now().isoformat()},
                            exc_info=True,
                        )
                        return False
                    # exponential backoff
                    time.sleep(backoff_seconds)
                    backoff_seconds *= 2
    except Exception:
        logger.exception('Ngrok notify: unexpected error during notification flow')
        return False