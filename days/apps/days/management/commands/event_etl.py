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
    succeeded = 0
    new = 0
    ignored = 0

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
                    'Retrieved %d events in %.2f seconds. Ignored %d events.',
                    self.succeeded,
                    elapsed,
                    self.ignored
                )

                if commit:
                    logger.info('Saved %d new events.', self.new)
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
        for event in events.children:
            if event == '\n':
                continue

            try:
                year, description = event.text.split(' – ', 1)
            except ValueError:
                self.ignored += 1
                logger.warning('Found a malformed entry: [%s]. Ignoring event.', event.text)

                continue

            if utils.is_alphabetic(year):
                self.ignored += 1
                # TODO: Figure out how to handle BC years. DateField and BooleanField combo?
                logger.warning('Found a year containing letters: [%s]. Ignoring event.', year)

                continue

            try:
                date = datetime.date(int(year), target.month, target.day)
            except ValueError:
                self.ignored += 1
                logger.warning(
                    'Unable to create date object for '
                    'year [%s], month [%s], day [%s]. Ignoring event.',
                    year,
                    target.month,
                    target.day
                )

                continue

            _, created = Event.objects.get_or_create(date=date, description=description)  # pylint: disable=no-member

            self.succeeded += 1
            self.new += 1 if created else 0
