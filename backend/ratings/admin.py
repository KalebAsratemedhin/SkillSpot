from django.contrib import admin
from .models import Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'rater', 'rated_user', 'rating_type', 'score',
        'job', 'contract', 'created_at'
    )
    list_filter = ('rating_type', 'score', 'created_at')
    search_fields = (
        'rater__email', 'rated_user__email', 'comment',
        'job__title', 'contract__title'
    )
    readonly_fields = ('id', 'created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'rater', 'rated_user', 'rating_type')
        }),
        ('Rating Details', {
            'fields': ('score', 'comment')
        }),
        ('Associated Items', {
            'fields': ('job', 'contract')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
