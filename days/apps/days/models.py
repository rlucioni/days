"""Models for the days app."""
from django.db import models


class Event(models.Model):
    """Representation of a notable historical event."""
    # How to perform lookups on this field: https://docs.djangoproject.com/en/1.9/ref/models/querysets/#month
    date = models.DateField(
        help_text='When the event occurred.'
    )

    description = models.TextField(
        help_text='A description of the event.'
    )

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta(object):  # pylint: disable=missing-docstring
        ordering = ['-modified']

    def __str__(self):
        return self.date.strftime('%b. %-d %Y')
