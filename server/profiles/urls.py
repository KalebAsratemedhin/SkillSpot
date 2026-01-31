from django.urls import path
from .views import (
    ProfileDetailView,
    ServiceProviderProfileView,
    TagListCreateView,
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
    path('tags/', TagListCreateView.as_view(), name='tag_list_create'),
    
    # Experiences
    path('experiences/', ExperienceListCreateView.as_view(), name='experience_list_create'),
    path('experiences/<uuid:id>/', ExperienceDetailView.as_view(), name='experience_detail'),
]
