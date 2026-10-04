from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'recipient', 'title', 'read', 'created_at')
    list_filter = ('read', 'created_at')
    search_fields = ('title', 'message', 'recipient__email')
    readonly_fields = ('id', 'created_at', 'read_at')
    raw_id_fields = ('recipient', 'actor')







