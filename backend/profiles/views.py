from rest_framework import generics, permissions, status
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.core.cache import cache
from skillspot.cache_utils import tags_list_cache_key, invalidate_tags_list, TAGS_LIST_TIMEOUT
from .models import Profile, ServiceProviderProfile, Tag, Experience
from .serializers import (
    ProfileSerializer,
    ServiceProviderProfileSerializer,
    ServiceProviderProfileUpdateSerializer,
    TagSerializer,
    ExperienceSerializer,
)

User = get_user_model()


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
            # Normalize to uppercase to match Tag.TagCategory (e.g. SKILL)
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
