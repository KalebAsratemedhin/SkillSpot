from django.contrib import admin
from .models import Job, JobApplication, JobInvitation


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'client', 'status', 'location',
        'budget_min', 'budget_max', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'location', 'client__email']
    filter_horizontal = ['required_skills']
    readonly_fields = ['id', 'created_at', 'updated_at', 'closed_at']


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'job', 'provider', 'status', 'proposed_rate', 'applied_at'
    ]
    list_filter = ['status', 'applied_at']
    search_fields = ['job__title', 'provider__email', 'cover_letter']
    readonly_fields = ['id', 'applied_at', 'reviewed_at']


@admin.register(JobInvitation)
class JobInvitationAdmin(admin.ModelAdmin):
    list_display = [
        'client', 'provider', 'job', 'status', 'invited_at'
    ]
    list_filter = ['status', 'invited_at']
    search_fields = ['client__email', 'provider__email', 'job__title']
    readonly_fields = ['id', 'invited_at', 'responded_at']
