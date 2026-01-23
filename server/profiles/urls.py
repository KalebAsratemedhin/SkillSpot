from django.urls import path
from .views import (
    ProfileDetailView,
    ServiceProviderProfileView,
    TagListView,
    ExperienceListCreateView,
    ExperienceDetailView,
)

app_name = 'profiles'

urlpatterns = [
    # Profile
    path('me/', ProfileDetailView.as_view(), name='profile_detail'),
    
    # Service Provider Profile
    path('provider/', ServiceProviderProfileView.as_view(), name='provider_profile'),
    
    # Tags (Skills, Certifications, Languages)
    path('tags/', TagListView.as_view(), name='tag_list'),
    
    # Experiences
    path('experiences/', ExperienceListCreateView.as_view(), name='experience_list_create'),
    path('experiences/<uuid:id>/', ExperienceDetailView.as_view(), name='experience_detail'),
]
