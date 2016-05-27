"""Management command for scraping historical events from Wikipedia."""
import calendar
from concurrent.futures import as_completed, ThreadPoolExecutor
import datetime
import logging

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
import requests

from days.apps.days.models import Event


logger = logging.getLogger(__name__)


class ForcedRollback(Exception):
    """Raised when intentionally rolling back a transaction."""
    pass


class Command(BaseCommand):
    """Management command for scraping historical events from Wikipedia."""
    help = 'Scrape historical events from Wikipedia.'
    url = 'https://en.wikipedia.org/wiki'
    leap_year = 2016

    def add_arguments(self, parser):
        parser.add_argument(
            '-t', '--target',
            action='store',
            dest='target',
            default=None,
            help=(
                'Specific month and day for which to scrape events, specified as a %%m-%%d formatted string.'
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
            targets = [datetime.datetime.strptime(target, '%m-%d').date()]
        else:
            if not calendar.isleap(self.leap_year):
                raise CommandError(
                    '{year} is not a leap year. '
                    'To guarantee that events for all possible days of a year are scraped, '
                    'the "leap_year" class variable must be set to a leap year.'.format(year=self.leap_year)
                )

            day_counts = [calendar.monthrange(self.leap_year, month)[1] for month in range(1, 13)]

            targets = []
            for month, day_count in enumerate(day_counts, start=1):
                for day in range(1, day_count + 1):
                    targets.append(
                        datetime.date(self.leap_year, month, day)
                    )

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self._scrape, t) for t in targets]

        try:
            with transaction.atomic():
                count = 0
                for future in as_completed(futures):
                    target, events = future.result()

                    logger.info('Processing events for %s', target.strftime('%B %-d'))

                    for event in events.children:
                        if event != '\n':
                            try:
                                year, description = event.text.split(' – ', 1)
                            except ValueError:
                                logger.warning('Found a malformed entry: [%s]. Ignoring event.', event.text)
                                continue

                            if any(c.isalpha() for c in year):
                                # TODO: Figure out how to handle BC years. DateField and BooleanField combo?
                                logger.warning('Found a year containing letters: [%s]. Ignoring event.', year)
                                continue

                            try:
                                date = datetime.date(int(year), target.month, target.day)
                            except ValueError:
                                logger.warning(
                                    'Unable to create date object for year [%s], month [%s], day [%s]. Ignoring event.',
                                    year,
                                    target.month,
                                    target.day
                                )
                                continue

                            Event.objects.create(date=date, description=description)  # pylint: disable=no-member

                            count += 1

                logger.info('Scraped %d events', count)

                if commit:
                    logger.info('Saved %d new events', count)
                else:
                    raise ForcedRollback(
                        'No data has been saved. To save data, pass the -c or --commit flags.'
                    )
        except ForcedRollback as e:
            logger.info(e)

    def _scrape(self, target):
        url = '{base_url}/{month_day}'.format(
            base_url=self.url,
            month_day=target.strftime('%B_%-d')
        )

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        uls = soup.find_all('ul')
        # TODO: February 29 has a slightly different structure. May need to grab third set of uls.
        events = uls[1]

        return target, events
