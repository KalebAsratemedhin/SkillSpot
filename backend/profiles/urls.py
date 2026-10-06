from django.urls import path
from .views import (
    ProfileDetailView,
    ServiceProviderProfileView,
    TagListCreateView,
    ExperienceListCreateView,
    ExperienceDetailView,
    PublicProviderListView,
    PublicProviderDetailView,
)

app_name = 'profiles'

urlpatterns = [
    # Public provider directory (must be before other patterns that could conflict)
    path('providers/', PublicProviderListView.as_view(), name='public_provider_list'),
    path(
        'providers/<uuid:user_id>/',
        PublicProviderDetailView.as_view(),
        name='public_provider_detail',
    ),

    # Own profile
    path('me/', ProfileDetailView.as_view(), name='profile_detail'),

    # Own service provider profile
    path('provider/', ServiceProviderProfileView.as_view(), name='provider_profile'),

    # Tags (Skills, Certifications, Languages)
    path('tags/', TagListCreateView.as_view(), name='tag_list_create'),

    # Experiences
    path('experiences/', ExperienceListCreateView.as_view(), name='experience_list_create'),
    path('experiences/<uuid:id>/', ExperienceDetailView.as_view(), name='experience_detail'),
]
