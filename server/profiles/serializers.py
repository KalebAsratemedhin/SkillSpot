from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile, ServiceProviderProfile, Tag, Experience

User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'category', 'description')
        read_only_fields = ('id',)


class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    user_type = serializers.CharField(source='user.user_type', read_only=True)
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Profile
        fields = (
            'id', 'email', 'user_type', 'first_name', 'last_name',
            'full_name', 'phone_number', 'avatar', 'bio', 'location',
            'address', 'timezone', 'is_verified', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data.get('first_name') and instance.user.first_name:
            data['first_name'] = instance.user.first_name
        if not data.get('last_name') and instance.user.last_name:
            data['last_name'] = instance.user.last_name
        return data

    def validate_avatar(self, value):
        if value:
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Image size cannot exceed 5MB.")
            if not value.content_type.startswith('image/'):
                raise serializers.ValidationError("File must be an image.")
        return value

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        if 'first_name' in validated_data or 'last_name' in validated_data:
            user = instance.user
            user.first_name = instance.first_name or ''
            user.last_name = instance.last_name or ''
            user.save(update_fields=['first_name', 'last_name'])
        return instance


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = (
            'id', 'title', 'company_name', 'description', 'location',
            'start_date', 'end_date', 'is_current',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate(self, attrs):
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        is_current = attrs.get('is_current', False)

        if end_date and start_date and end_date < start_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date.'
            })
        
        if is_current and end_date:
            raise serializers.ValidationError({
                'is_current': 'Current position cannot have an end date.'
            })
        
        return attrs


class ServiceProviderProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    skills = TagSerializer(many=True, read_only=True)
    certifications = TagSerializer(many=True, read_only=True)
    languages = TagSerializer(many=True, read_only=True)
    experiences = ExperienceSerializer(many=True, read_only=True)
    
    skill_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.filter(category=Tag.TagCategory.SKILL),
        write_only=True,
        required=False,
        source='skills'
    )
    certification_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.filter(category=Tag.TagCategory.CERTIFICATION),
        write_only=True,
        required=False,
        source='certifications'
    )
    language_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.filter(category=Tag.TagCategory.LANGUAGE),
        write_only=True,
        required=False,
        source='languages'
    )

    class Meta:
        model = ServiceProviderProfile
        fields = (
            'id', 'profile', 'hourly_rate', 'availability_status',
            'years_of_experience', 'service_radius', 'skills',
            'certifications', 'languages', 'skill_ids', 'certification_ids',
            'language_ids', 'portfolio_visibility', 'total_jobs_completed',
            'average_rating', 'total_earnings', 'experiences',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'total_jobs_completed', 'average_rating',
            'total_earnings', 'created_at', 'updated_at'
        )


class ServiceProviderProfileUpdateSerializer(serializers.ModelSerializer):
    skill_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.filter(category=Tag.TagCategory.SKILL),
        required=False,
        source='skills'
    )
    certification_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.filter(category=Tag.TagCategory.CERTIFICATION),
        required=False,
        source='certifications'
    )
    language_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.filter(category=Tag.TagCategory.LANGUAGE),
        required=False,
        source='languages'
    )

    class Meta:
        model = ServiceProviderProfile
        fields = (
            'hourly_rate', 'availability_status', 'years_of_experience',
            'service_radius', 'skill_ids', 'certification_ids',
            'language_ids', 'portfolio_visibility'
        )
