"""ETL utility for retrieving historical events from Wikipedia."""
from concurrent.futures import as_completed, ThreadPoolExecutor
import datetime
import logging
import time

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
import requests

from days.apps.days import utils
from days.apps.days.models import Event


logger = logging.getLogger(__name__)


class ForcedRollback(Exception):
    """Raised when intentionally rolling back a transaction."""
    pass


class Command(BaseCommand):
    """ETL utility for retrieving historical events from Wikipedia."""
    help = 'ETL utility for retrieving historical events from Wikipedia.'
    url = 'https://en.wikipedia.org/wiki'
    # For targeting February 29.
    leap_year = settings.LEAP_YEAR
    loaded = 0
    ignored = 0
    new = 0
    updated = 0
    deleted = 0

    def add_arguments(self, parser):
        parser.add_argument(
            '-t', '--target',
            action='store',
            dest='target',
            default=None,
            help=(
                'Specific month and day for which to retrieve events, specified as a %%m-%%d formatted string.'
            )
        )

        parser.add_argument(
            '-c', '--commit',
            action='store_true',
            dest='commit',
            default=False,
            help='Save event data to the database. By default, no data is saved.'
        )

    def handle(self, *args, **options):
        target = options.get('target')
        commit = options.get('commit')

        if target:
            targets = [
                datetime.datetime.strptime(
                    '{leap_year}-{target}'.format(leap_year=self.leap_year, target=target),
                    '%Y-%m-%d'
                ).date()
            ]
        else:
            targets = utils.all_days()  # pylint: disable=redefined-variable-type

        start = time.time()
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.scrape, t) for t in targets]

        try:
            with transaction.atomic():
                for future in as_completed(futures):
                    target, response = future.result()

                    logger.debug('Processing events for %s.', target.strftime('%B %-d'))

                    events = self.parse(target, response)
                    self.load(target, events)

                end = time.time()
                elapsed = end - start
                logger.info(
                    'Loaded %d events in %.2f seconds. Ignored %d others. '
                    '%d events are new. %d existing events will be updated. '
                    '%d existing events will be deleted.',
                    self.loaded,
                    elapsed,
                    self.ignored,
                    self.new,
                    self.updated,
                    self.deleted,
                )

                if commit:
                    logger.info(
                        'Saved %d new events. %d existing events were updated. '
                        '%d existing events were deleted.',
                        self.new,
                        self.updated,
                        self.deleted,
                    )
                else:
                    raise ForcedRollback(
                        'No data has been saved. To save data, pass the -c or --commit flags.'
                    )
        except ForcedRollback as e:
            logger.info(e)

    def scrape(self, target):
        """GET the given day's page from Wikipedia."""
        url = '{base_url}/{month_day}'.format(
            base_url=self.url,
            month_day=target.strftime('%B_%-d')
        )

        response = requests.get(url)

        return target, response

    def parse(self, target, response):  # pylint: disable=no-self-use
        """Extract the unordered list of events."""
        soup = BeautifulSoup(response.text, 'html.parser')
        uls = soup.find_all('ul')

        # The page for February 29 has a slightly different structure.
        if utils.is_leap_day(target):
            events = uls[3]
        else:
            events = uls[1]

        return events

    def load(self, target, events):
        """Load parsed events into the database."""
        old_events = Event.objects.filter(date__month=target.month, date__day=target.day)

        for event in events.children:
            if event == '\n':
                continue

            try:
                year, description = event.text.split(' – ', 1)
            except ValueError:
                self.ignored += 1
                logger.warning(
                    'Found a malformed entry: [%s]. Ignoring event for %s.',
                    event.text,
                    target.strftime('%B %-d')
                )

                continue

            if utils.is_alphabetic(year):
                self.ignored += 1
                # TODO: Figure out how to handle BC years. DateField and BooleanField combo?
                logger.warning(
                    'Found a year containing letters: [%s]. Ignoring event for %s.',
                    year,
                    target.strftime('%B %-d')
                )

                continue

            try:
                date = datetime.date(int(year), target.month, target.day)
            except ValueError:
                self.ignored += 1
                logger.warning(
                    'Unable to create date object from '
                    'year [%s], month [%s], day [%s]. Ignoring event.',
                    year,
                    target.month,
                    target.day
                )

                continue

            old_events = self.update_or_create(date, description, old_events)

        self.delete(old_events)

    def update_or_create(self, date, description, old_events):
        """Update an existing event's description or create a new one."""
        olds = old_events.filter(date__year=date.year)
        for old in olds:
            # Do we already have the event?
            if old.description == description:
                # Prevent it from being deleted.
                old_events = old_events.exclude(id=old.id)
                break
            # Do we have an event with a very similar description?
            elif utils.are_similar(old.description, description):
                # Prefer what is likely the latest description of the event.
                old.description = description
                old.save()
                self.updated += 1

                # Prevent the updated event from being deleted.
                old_events = old_events.exclude(id=old.id)
                break
        else:
            # This appears to be a new event.
            event = Event.objects.create(date=date, description=description)
            self.new += 1

            # Prevent the new event from being deleted.
            old_events = old_events.exclude(id=event.id)

        self.loaded += 1

        return old_events

    def delete(self, old_events):
        """Delete events no longer listed on Wikipedia."""
        self.deleted += len(old_events)
        old_events.delete()
