from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.contrib.auth import get_user_model
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


class TagListView(generics.ListAPIView):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Tag.objects.all()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        return queryset


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
