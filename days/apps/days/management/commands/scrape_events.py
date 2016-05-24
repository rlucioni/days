import logging

from bs4 import BeautifulSoup
from django.conf import settings
from django.core.management import BaseCommand
import requests

# TODO: Implement models.
# from days.apps.days.models import Event


logger = logging.getLogger(__name__)
url = 'https://en.wikipedia.org/wiki/May_21'

class Command(BaseCommand):
    help = 'Scrape historical events from Wikipedia.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--commit',
            action='store_true',
            dest='commit',
            default=False,
            help='Save event data to the database.'
        )

    def handle(self, *args, **options):
        commit = options.get('commit')

        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        uls = soup.find_all('ul')
        events_section = uls[1]

        events = []
        for event in events_section.children:
            if event != '\n':
                # http://www.fileformat.info/info/unicode/char/2013/index.htm
                events.append(event.text.split(' – '))

        logger.info('Scraped %d events', len(events))
