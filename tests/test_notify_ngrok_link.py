from unittest import mock
from django.test import TestCase, override_settings
from django.core import mail

from sales.services.notification import send_ngrok_link_notification


class NotifyNgrokLinkTests(TestCase):
    def setUp(self):
        from django.core.cache import cache
        cache.clear()
        self.url = 'https://example.ngrok-free.app'

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='no-reply@example.com')
    @mock.patch.dict('os.environ', {
        'NGROK_NOTIFY_ENABLED': 'True',
        'NGROK_NOTIFY_EMAILS': 'a@example.com,b@example.com',
        'NGROK_NOTIFY_SUBJECT': 'POS is up — your POS ngrok URL',
        'NGROK_NOTIFY_SEND_RETRIES': '1',
    }, clear=False)
    def test_sends_email_with_url_and_subject(self):
        ok = send_ngrok_link_notification(self.url)
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 1)
        message = mail.outbox[0]
        self.assertEqual(message.subject, 'POS is up — your POS ngrok URL')
        self.assertListEqual(sorted(message.to), ['a@example.com', 'b@example.com'])
        self.assertIn(self.url, message.body)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='no-reply@example.com')
    @mock.patch.dict('os.environ', {
        'NGROK_NOTIFY_ENABLED': 'False',
        'NGROK_NOTIFY_EMAILS': 'a@example.com',
    }, clear=False)
    def test_skips_when_disabled(self):
        ok = send_ngrok_link_notification(self.url)
        self.assertTrue(ok)
        self.assertEqual(len(mail.outbox), 0)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='no-reply@example.com')
    @mock.patch.dict('os.environ', {
        'NGROK_NOTIFY_ENABLED': 'True',
        'NGROK_NOTIFY_EMAILS': 'a@example.com',
        'NGROK_NOTIFY_SEND_RETRIES': '2',
    }, clear=False)
    @mock.patch('sales.services.notification.EmailMultiAlternatives.send')
    def test_retries_on_failure(self, mock_send):
        # first raises twice, then success
        mock_send.side_effect = [Exception('smtp down'), Exception('smtp still down'), None]
        ok = send_ngrok_link_notification(self.url)
        self.assertTrue(ok)
        self.assertGreaterEqual(mock_send.call_count, 3)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend', DEFAULT_FROM_EMAIL='no-reply@example.com')
    @mock.patch.dict('os.environ', {
        'NGROK_NOTIFY_ENABLED': 'True',
        'NGROK_NOTIFY_EMAILS': 'a@example.com',
    }, clear=False)
    def test_idempotency_skips_duplicate_within_window(self):
        ok1 = send_ngrok_link_notification(self.url)
        ok2 = send_ngrok_link_notification(self.url)
        self.assertTrue(ok1)
        self.assertTrue(ok2)
        # only first should actually send
        from django.core import mail
        self.assertEqual(len(mail.outbox), 1)