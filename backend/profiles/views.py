from rest_framework import generics, permissions, filters
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Count, Q, Case, When, IntegerField, Value
from skillspot.cache_utils import (
    tags_list_cache_key,
    invalidate_tags_list,
    TAGS_LIST_TIMEOUT,
    provider_list_cache_key,
    PROVIDER_LIST_TIMEOUT,
)
from .models import Profile, ServiceProviderProfile, Tag, Experience
from .serializers import (
    ProfileSerializer,
    ServiceProviderProfileSerializer,
    ServiceProviderProfileUpdateSerializer,
    TagSerializer,
    ExperienceSerializer,
    PublicProviderListSerializer,
    PublicProviderDetailSerializer,
)
from ratings.models import Rating

User = get_user_model()


def _parse_skill_ids(request):
    ids = []
    for key in ('skill', 'skills'):
        ids.extend(request.query_params.getlist(key))
    for raw in list(ids):
        if ',' in raw:
            ids.remove(raw)
            ids.extend(part.strip() for part in raw.split(',') if part.strip())
    return [s for s in ids if s]


def _public_provider_queryset():
    return (
        ServiceProviderProfile.objects.filter(
            portfolio_visibility=True,
            profile__user__is_active=True,
            profile__user__user_type__in=['PROVIDER', 'BOTH'],
        )
        .select_related('profile', 'profile__user')
        .prefetch_related('skills', 'certifications', 'languages', 'experiences')
        .annotate(
            rating_count=Count(
                'profile__user__ratings_received',
                filter=Q(
                    profile__user__ratings_received__rating_type=Rating.RatingType.CLIENT_TO_PROVIDER
                ),
            )
        )
    )


class PublicProviderListView(generics.ListAPIView):
    """Public provider directory — AllowAny, no PII."""
    serializer_class = PublicProviderListSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['hourly_rate', 'average_rating']
    ordering = ['-average_rating']

    def get_queryset(self):
        qs = _public_provider_queryset()
        params = self.request.query_params

        q = (params.get('q') or params.get('search') or '').strip()
        if q:
            qs = qs.filter(
                Q(profile__first_name__icontains=q)
                | Q(profile__last_name__icontains=q)
                | Q(profile__bio__icontains=q)
                | Q(profile__location__icontains=q)
                | Q(skills__name__icontains=q)
            )
            qs = qs.annotate(
                _relevance=Case(
                    When(
                        Q(profile__first_name__icontains=q)
                        | Q(profile__last_name__icontains=q),
                        then=Value(3),
                    ),
                    When(skills__name__icontains=q, then=Value(2)),
                    default=Value(1),
                    output_field=IntegerField(),
                )
            )

        location = params.get('location')
        if location:
            qs = qs.filter(profile__location__icontains=location)

        skill_ids = _parse_skill_ids(self.request)
        if skill_ids:
            qs = qs.filter(skills__id__in=skill_ids)

        rate_min = params.get('hourly_rate_min')
        if rate_min:
            qs = qs.filter(hourly_rate__gte=rate_min)
        rate_max = params.get('hourly_rate_max')
        if rate_max:
            qs = qs.filter(hourly_rate__lte=rate_max)

        availability = params.get('availability')
        if availability:
            qs = qs.filter(availability_status=availability.upper())

        is_verified = params.get('is_verified')
        if is_verified is not None and is_verified != '':
            truthy = is_verified.lower() in ('1', 'true', 'yes')
            qs = qs.filter(profile__is_verified=truthy)

        ordering = params.get('ordering')
        if q and (not ordering or ordering == 'relevance'):
            qs = qs.order_by('-_relevance', '-average_rating')
        elif ordering == '-rating':
            qs = qs.order_by('-average_rating', '-rating_count')
        elif ordering == 'hourly_rate':
            qs = qs.order_by('hourly_rate')
        elif ordering == '-hourly_rate':
            qs = qs.order_by('-hourly_rate')
        elif ordering == '-member_since':
            qs = qs.order_by('-profile__created_at')
        elif ordering == 'member_since':
            qs = qs.order_by('profile__created_at')

        return qs.distinct()

    def list(self, request, *args, **kwargs):
        key = provider_list_cache_key(request)
        data = cache.get(key)
        if data is not None:
            return Response(data)
        response = super().list(request, *args, **kwargs)
        cache.set(key, response.data, timeout=PROVIDER_LIST_TIMEOUT)
        return response


class PublicProviderDetailView(generics.RetrieveAPIView):
    """Public provider profile by user_id — AllowAny, no PII."""
    serializer_class = PublicProviderDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'profile__user_id'
    lookup_url_kwarg = 'user_id'

    def get_queryset(self):
        return _public_provider_queryset()


class ProfileDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    http_method_names = ['get', 'patch']

    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile


class ServiceProviderProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ServiceProviderProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ['get', 'patch']

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        provider_profile, created = ServiceProviderProfile.objects.get_or_create(
            profile=profile
        )
        return provider_profile

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return ServiceProviderProfileUpdateSerializer
        return ServiceProviderProfileSerializer


class TagListCreateView(generics.ListCreateAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Tag.objects.all().order_by('name')
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category.upper())
        return queryset

    def list(self, request, *args, **kwargs):
        if request.method != 'GET':
            return super().list(request, *args, **kwargs)
        category = request.query_params.get('category')
        key = tags_list_cache_key(category.upper() if category else None)
        data = cache.get(key)
        if data is not None:
            return Response(data)
        response = super().list(request, *args, **kwargs)
        cache.set(key, response.data, timeout=TAGS_LIST_TIMEOUT)
        return response

    def perform_create(self, serializer):
        serializer.save()
        invalidate_tags_list()


class ExperienceListCreateView(generics.ListCreateAPIView):
    serializer_class = ExperienceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        provider_profile, _ = ServiceProviderProfile.objects.get_or_create(
            profile=profile
        )
        return Experience.objects.filter(provider=provider_profile)

    def perform_create(self, serializer):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        provider_profile, _ = ServiceProviderProfile.objects.get_or_create(
            profile=profile
        )
        serializer.save(provider=provider_profile)


class ExperienceDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ExperienceSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    http_method_names = ['get', 'patch', 'delete']

    def get_queryset(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        provider_profile, _ = ServiceProviderProfile.objects.get_or_create(
            profile=profile
        )
        return Experience.objects.filter(provider=provider_profile)
