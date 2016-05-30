"""Django admin configuration for days models."""
from django.contrib import admin

from days.apps.days.models import Event, Subscriber


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin config for the Event model."""
    list_display = ('date', 'description', 'created', 'modified')
    search_fields = ('description',)
    show_full_result_count = False

    fields = ('date', 'description', 'created', 'modified')
    readonly_fields = ('created', 'modified')


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    """Admin config for the Subscriber model."""
    list_display = ('email', 'created', 'modified')
    search_fields = ('email',)
    show_full_result_count = False

    fields = ('email', 'created', 'modified')
    readonly_fields = ('created', 'modified')
