"""App configuration."""
import calendar

from django.apps import AppConfig
from django.conf import settings


class DaysConfig(AppConfig):
    """Configuration for the days app."""
    name = 'days.apps.days'

    def ready(self):
        if not calendar.isleap(settings.LEAP_YEAR):
            raise RuntimeError(
                '{year} is not a leap year. '
                'To guarantee that events for all possible days of a year can be retrieved, '
                'set LEAP_YEAR to a leap year.'.format(year=settings.LEAP_YEAR)
            )
