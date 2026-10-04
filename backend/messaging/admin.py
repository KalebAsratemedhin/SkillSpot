from django.contrib import admin
from .models import Conversation, Message, MessageAttachment


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'participant1', 'participant2', 'job', 'last_message_at', 'created_at')
    list_filter = ('created_at', 'last_message_at')
    search_fields = ('participant1__email', 'participant2__email', 'job__title')
    readonly_fields = ('id', 'created_at', 'updated_at', 'last_message_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'participant1', 'participant2', 'job')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_message_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'sender', 'content_preview', 'is_read', 'read_at', 'created_at')
    list_filter = ('is_read', 'created_at', 'read_at')
    search_fields = ('content', 'sender__email', 'conversation__id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'read_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'conversation', 'sender', 'content')
        }),
        ('Read Status', {
            'fields': ('is_read', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'message', 'file_name', 'file_size', 'file_type', 'created_at')
    list_filter = ('file_type', 'created_at')
    search_fields = ('file_name', 'message__id')
    readonly_fields = ('id', 'created_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'message', 'file', 'file_name')
        }),
        ('File Details', {
            'fields': ('file_size', 'file_type')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
