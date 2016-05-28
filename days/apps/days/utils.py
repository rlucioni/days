"""Utility functions."""
import calendar
import datetime

from django.conf import settings


def all_days(self):
    """Generator yielding all possible days of a year."""
    day_counts = [calendar.monthrange(settings.LEAP_YEAR, month)[1] for month in range(1, 13)]

    for month, day_count in enumerate(day_counts, start=1):
        for day in range(1, day_count + 1):
            yield datetime.date(settings.LEAP_YEAR, month, day)


def is_alphabetic(string):
    """Check if the given string contains alphabetic characters."""
    return any(c.isalpha() for c in string)


def is_leap_day(date):
    """Check if the given date is a leap day."""
    return date.month == 2 and date.day == 29
