from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q, Avg, Count
from notifications.tasks import send_in_app_notification
from .models import Rating
from .serializers import (
    RatingSerializer,
    RatingCreateSerializer,
    RatingUpdateSerializer,
    UserRatingStatsSerializer,
)

User = get_user_model()


class RatingListCreateView(generics.ListCreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, filters.SearchFilter]
    ordering_fields = ['created_at', 'score']
    ordering = ['-created_at']
    search_fields = ['comment']

    def get_queryset(self):
        queryset = Rating.objects.all()

        # Filter by rated user
        rated_user_id = self.request.query_params.get('rated_user', None)
        if rated_user_id:
            queryset = queryset.filter(rated_user_id=rated_user_id)

        # Filter by rater
        rater_id = self.request.query_params.get('rater', None)
        if rater_id:
            queryset = queryset.filter(rater_id=rater_id)

        # Filter by rating type
        rating_type = self.request.query_params.get('rating_type', None)
        if rating_type:
            queryset = queryset.filter(rating_type=rating_type)

        # Filter by job
        job_id = self.request.query_params.get('job', None)
        if job_id:
            queryset = queryset.filter(job_id=job_id)

        # Filter by contract
        contract_id = self.request.query_params.get('contract', None)
        if contract_id:
            queryset = queryset.filter(contract_id=contract_id)

        # Filter by user's own ratings (given or received)
        my_ratings = self.request.query_params.get('my_ratings', None)
        if my_ratings == 'true':
            queryset = queryset.filter(
                Q(rater=self.request.user) | Q(rated_user=self.request.user)
            )

        return queryset.distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return RatingCreateSerializer
        return RatingSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['rater'] = self.request.user
        return context

    def perform_create(self, serializer):
        rating = serializer.save(rater=self.request.user)
        link = f'/contracts/{rating.contract_id}/' if rating.contract_id else (f'/jobs/{rating.job_id}/' if rating.job_id else '/profile')
        send_in_app_notification.delay(
            str(rating.rated_user_id),
            'New review',
            f'You received a {rating.score}-star review.',
            link=link,
            actor_id=str(self.request.user.id),
        )


class RatingDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        user = self.request.user
        # Users can only view/update/delete their own ratings
        return Rating.objects.filter(rater=user)

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return RatingUpdateSerializer
        return RatingSerializer

    def update(self, request, *args, **kwargs):
        # Only allow updating score and comment
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(RatingSerializer(instance).data)


class UserRatingStatsView(generics.GenericAPIView):
    """
    Get rating statistics for a user
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, user_id=None):
        # If user_id not provided, use current user
        if not user_id:
            user_id = request.user.id
        else:
            user_id = user_id

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Calculate ratings as provider
        provider_ratings = Rating.objects.filter(
            rated_user=user,
            rating_type=Rating.RatingType.CLIENT_TO_PROVIDER
        )
        provider_stats = provider_ratings.aggregate(
            average=Avg('score'),
            count=Count('id')
        )

        # Calculate ratings as client
        client_ratings = Rating.objects.filter(
            rated_user=user,
            rating_type=Rating.RatingType.PROVIDER_TO_CLIENT
        )
        client_stats = client_ratings.aggregate(
            average=Avg('score'),
            count=Count('id')
        )

        # Get user name
        user_name = user.email
        if hasattr(user, 'profile') and user.profile:
            user_name = user.profile.full_name

        data = {
            'user_id': str(user.id),
            'user_email': user.email,
            'user_name': user_name,
            'average_rating_as_provider': round(provider_stats['average'] or 0, 2),
            'rating_count_as_provider': provider_stats['count'] or 0,
            'average_rating_as_client': round(client_stats['average'] or 0, 2),
            'rating_count_as_client': client_stats['count'] or 0,
            'total_ratings': (provider_stats['count'] or 0) + (client_stats['count'] or 0),
        }

        return Response(data, status=status.HTTP_200_OK)


class ProviderRatingsView(generics.ListAPIView):
    """
    Get all ratings for a provider (client to provider ratings)
    """
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        provider_id = self.kwargs.get('provider_id')
        return Rating.objects.filter(
            rated_user_id=provider_id,
            rating_type=Rating.RatingType.CLIENT_TO_PROVIDER
        ).order_by('-created_at')


class ClientRatingsView(generics.ListAPIView):
    """
    Get all ratings for a client (provider to client ratings)
    """
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        client_id = self.kwargs.get('client_id')
        return Rating.objects.filter(
            rated_user_id=client_id,
            rating_type=Rating.RatingType.PROVIDER_TO_CLIENT
        ).order_by('-created_at')
