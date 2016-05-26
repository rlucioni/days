"""Models for the days app."""
from django.db import models


class Event(models.Model):
    """Representation of a notable historical event."""
    date = models.DateField(
        help_text='When the event occurred.'
    )

    description = models.TextField(
        help_text='A description of the event.'
    )
