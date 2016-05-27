"""Management command for scraping historical events from Wikipedia."""
from concurrent.futures import as_completed, ThreadPoolExecutor
import datetime
import logging

from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from tqdm import tqdm
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

    def add_arguments(self, parser):
        parser.add_argument(
            '-t', '--target',
            action='store',
            dest='target',
            default=None,
            help=(
                'Month and day for which to scrape events, specified as a %%m-%%d formatted string. '
                'Defaults to the current date (UTC).'
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
            targets = [timezone.now().date()]

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(self._scrape, t) for t in targets]

        tqdm_kwargs = {
            'total': len(futures),
            'unit': 'pages',
            'unit_scale': True,
            'leave': True
        }

        try:
            with transaction.atomic():
                count = 0
                for future in tqdm(as_completed(futures), **tqdm_kwargs):
                    target, events = future.result()

                    for event in events.children:
                        if event != '\n':
                            year, description = event.text.split(' – ', 1)

                            if any(c.isalpha() for c in year):
                                # TODO: Figure out how to handle BC years. DateField and BooleanField combo?
                                logger.debug('Found a year containing letters: [%s]. Ignoring event.', year)
                                continue

                            date = datetime.date(int(year), target.month, target.day)
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
        events = uls[1]

        return target, events
