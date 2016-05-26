"""Django admin configuration for days models."""
from django.contrib import admin

from days.apps.days.models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin config for the Event model."""
    list_display = ('date', 'description')
    search_fields = ('description',)
    show_full_result_count = False
