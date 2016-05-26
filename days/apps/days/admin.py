from django.contrib import admin

from days.apps.days.models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('date', 'description')
    search_fields = ('description',)
    show_full_result_count = False
