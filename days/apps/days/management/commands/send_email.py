"""Email events to subscribers."""
from concurrent.futures import as_completed, ThreadPoolExecutor
import logging
import random

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
import sendgrid

from days.apps.days.models import Event, Subscriber


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Email events to subscribers."""
    help = 'Email events to subscribers.'
    sg = None
    today = None
    events = None

    def add_arguments(self, parser):
        parser.add_argument(
            '-e', '--email',
            action='store',
            dest='email',
            default=None,
            help=('Email address identifying a specific subscriber to which to send email.')
        )

    def handle(self, *args, **options):
        email = options.get('email')

        self.sg = sendgrid.SendGridClient(
            settings.SENDGRID_USERNAME,
            settings.SENDGRID_PASSWORD,
        )

        if email:
            subscribers = [Subscriber.objects.get(email=email)]
        else:
            subscribers = Subscriber.objects.all()

        self.get_events()

        subject = '{date} - On This Day'.format(date=self.today.strftime('%B %-d'))
        lines = ['{year}: {description}'.format(year=e.date.year, description=e.description) for e in self.events]
        text = '\n'.join(lines)

        messages = [
            sendgrid.Mail(
                to=s.email,
                subject=subject,
                # html='html',
                text=text,
                from_email=settings.FROM_EMAIL,
            ) for s in subscribers
        ]

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.sg.send, m) for m in messages]

        for future in as_completed(futures):
            status, msg = future.result()
            log_msg = 'SendGrid returned {status}: {msg}.'.format(status=status, msg=msg)
            logger.debug(log_msg) if status == 200 else logger.error(log_msg)

    def get_events(self):
        """Get events to include in emails."""
        self.today = timezone.now()
        candidates = Event.objects.filter(date__month=self.today.month, date__day=self.today.day)

        try:
            events = random.sample(list(candidates), settings.EVENT_COUNT)
            self.events = sorted(events, key=lambda e: e.date)
        # Sample larger than population
        except ValueError:
            self.events = candidates
