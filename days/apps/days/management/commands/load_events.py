"""Retrieve historical events from Wikipedia."""
import calendar
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
from days.apps.days.exceptions import ForcedRollback
from days.apps.days.models import Event


logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Retrieve historical events from Wikipedia."""
    help = 'Retrieve historical events from Wikipedia.'
    load_day = calendar.day_name[settings.LOAD_DAY]
    url = 'https://en.wikipedia.org/wiki'
    ignored = 0
    new = 0
    deleted = 0

    def add_arguments(self, parser):
        parser.add_argument(
            '-f', '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Force execution. By default, the command only runs on {}.'.format(self.load_day)
        )

        parser.add_argument(
            '-c', '--commit',
            action='store_true',
            dest='commit',
            default=False,
            help='Save event data to the database. By default, no data is saved.'
        )

    def handle(self, *args, **options):
        force = options.get('force')
        commit = options.get('commit')

        if not self.is_runnable(force):
            return

        start = time.time()
        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.scrape, day) for day in utils.date_range()]

        try:
            with transaction.atomic():
                self.delete()

                for future in as_completed(futures):
                    day, response = future.result()

                    logger.debug('Processing events for %s.', day.strftime('%B %-d'))

                    events = self.parse(day, response)
                    self.load(day, events)

                end = time.time()
                elapsed = end - start
                logger.info(
                    'Loaded %d events in %.2f seconds. Ignored %d others. '
                    '%d existing events will be deleted.',
                    self.new,
                    elapsed,
                    self.ignored,
                    self.deleted,
                )

                if commit:
                    logger.info(
                        'Saved %d new events. Deleted %d existing events.',
                        self.new,
                        self.deleted,
                    )
                else:
                    raise ForcedRollback(
                        'No data has been saved. To save data, pass the -c or --commit flags.'
                    )
        except ForcedRollback as e:
            logger.info(e)

    def is_runnable(self, force):
        """Determine if the command should be run."""
        if force:
            return True
        else:
            weekday = datetime.datetime.now().weekday()
            if weekday == settings.LOAD_DAY:
                return True
            else:
                logger.info(
                    'Today is %s. This command only runs on %s. Exiting.',
                    calendar.day_name[weekday],
                    self.load_day,
                )
                return False

    def scrape(self, day):
        """GET the given day's page from Wikipedia."""
        url = '{base_url}/{month_day}'.format(
            base_url=self.url,
            month_day=day.strftime('%B_%-d')
        )

        response = requests.get(url)

        return day, response

    def delete(self):
        """Delete existing events."""
        existing = Event.objects.all()
        self.deleted = len(existing)

        existing.delete()

    def parse(self, day, response):  # pylint: disable=no-self-use
        """Extract the unordered list of events."""
        soup = BeautifulSoup(response.text, 'html.parser')
        uls = soup.find_all('ul')

        # The page for February 29 has a slightly different structure.
        if utils.is_leap_day(day):
            events = uls[3]
        else:
            events = uls[1]

        return events

    def load(self, day, events):
        """Load parsed events into the database."""
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
                    day.strftime('%B %-d')
                )

                continue

            if utils.is_alphabetic(year):
                self.ignored += 1
                # TODO: Figure out how to handle BC years. DateField and BooleanField combo?
                logger.warning(
                    'Found a year containing letters: [%s]. Ignoring event for %s.',
                    year,
                    day.strftime('%B %-d')
                )

                continue

            try:
                date = datetime.date(int(year), day.month, day.day)
            except ValueError:
                self.ignored += 1
                logger.warning(
                    'Unable to create date object from '
                    'year [%s], month [%s], day [%s]. Ignoring event.',
                    year,
                    day.month,
                    day.day
                )

                continue

            Event.objects.create(date=date, description=description)
            self.new += 1
