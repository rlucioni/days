"""Utility functions."""
import datetime

from django.conf import settings


def date_range():
    """Generator yielding a range of future dates."""
    now = datetime.datetime.now()
    return (now + datetime.timedelta(days=days) for days in range(settings.DAY_COUNT))


def is_alphabetic(string):
    """Check if the given string contains alphabetic characters."""
    return any(c.isalpha() for c in string)


def is_leap_day(date):
    """Check if the given date is a leap day."""
    return date.month == 2 and date.day == 29
