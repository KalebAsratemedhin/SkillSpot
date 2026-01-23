from django.contrib import admin
from .models import Profile, ServiceProviderProfile, Tag, Experience


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'location', 'phone_number', 'is_verified', 'created_at']
    list_filter = ['is_verified', 'created_at']
    search_fields = ['user__email', 'first_name', 'last_name', 'location']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ServiceProviderProfile)
class ServiceProviderProfileAdmin(admin.ModelAdmin):
    list_display = [
        'profile', 'hourly_rate', 'availability_status',
        'years_of_experience', 'service_radius', 'average_rating',
        'total_jobs_completed'
    ]
    list_filter = ['availability_status', 'portfolio_visibility', 'created_at']
    search_fields = ['profile__user__email', 'profile__location']
    filter_horizontal = ['skills', 'certifications', 'languages']
    readonly_fields = ['id', 'total_jobs_completed', 'average_rating', 'total_earnings', 'created_at', 'updated_at']


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at']


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'company_name', 'provider', 'location',
        'start_date', 'end_date', 'is_current'
    ]
    list_filter = ['is_current', 'start_date']
    search_fields = ['title', 'company_name', 'location', 'provider__profile__user__email']
    readonly_fields = ['id', 'created_at', 'updated_at']
