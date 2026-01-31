from django.urls import path
from .views import (
    RatingListCreateView,
    RatingDetailView,
    UserRatingStatsView,
    ProviderRatingsView,
    ClientRatingsView,
)

app_name = 'ratings'

urlpatterns = [
    path('', RatingListCreateView.as_view(), name='rating_list_create'),
    path('<uuid:id>/', RatingDetailView.as_view(), name='rating_detail'),
    path('stats/<uuid:user_id>/', UserRatingStatsView.as_view(), name='user_rating_stats'),
    path('stats/', UserRatingStatsView.as_view(), name='current_user_rating_stats'),
    path('providers/<uuid:provider_id>/', ProviderRatingsView.as_view(), name='provider_ratings'),
    path('clients/<uuid:client_id>/', ClientRatingsView.as_view(), name='client_ratings'),
]
