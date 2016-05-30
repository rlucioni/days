"""Email events to subscribers."""
import logging
import random

from django.conf import settings
from django.core.mail import send_mass_mail
from django.core.management.base import BaseCommand
from django.utils import timezone

from days.apps.days.models import Event, Subscriber


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Email events to subscribers."""
    help = 'Email events to subscribers.'

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

        if email:
            subscribers = [Subscriber.objects.get(email=email)]
        else:
            subscribers = Subscriber.objects.all()

        today = timezone.now()
        candidates = Event.objects.filter(date__month=today.month, date__day=today.day)

        try:
            events = random.sample(list(candidates), settings.EVENT_COUNT)
            events = sorted(events, key=lambda e: e.date)
        # Sample larger than population
        except ValueError:
            events = candidates

        subject = 'On This Day'

        lines = ['{year} - {description}'.format(year=e.date.year, description=e.description) for e in events]
        message = '\n'.join(lines)

        from_email = 'from@example.com'

        emails = [(subject, message, from_email, [s.email]) for s in subscribers]

        send_mass_mail(emails)
