from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile, ServiceProviderProfile, Tag, Experience
from ratings.models import Rating

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
        request = self.context.get('request')
        if request and instance.avatar:
            data['avatar'] = request.build_absolute_uri(instance.avatar.url)
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


# --- Public provider directory (no email, phone, address, Stripe) ---

def _absolute_avatar(request, profile):
    if not profile or not profile.avatar:
        return None
    if request:
        return request.build_absolute_uri(profile.avatar.url)
    return profile.avatar.url


def _public_display_name(profile):
    if profile and (profile.first_name or profile.last_name):
        return f'{profile.first_name} {profile.last_name}'.strip()
    return ''


def _provider_rating_payload(provider_profile, rating_count=None):
    avg = provider_profile.average_rating
    count = rating_count
    if count is None:
        count = Rating.calculate_average_rating(
            provider_profile.profile.user,
            rating_type=Rating.RatingType.CLIENT_TO_PROVIDER,
        )['count'] or 0
    if not count:
        return {'average': None, 'count': 0}
    return {
        'average': float(avg) if avg is not None else None,
        'count': count,
    }


class PublicProviderListSerializer(serializers.Serializer):
    """Lean public card for provider directory."""

    user_id = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    location = serializers.SerializerMethodField()
    headline_skills = serializers.SerializerMethodField()
    hourly_rate = serializers.SerializerMethodField()
    availability = serializers.CharField(source='availability_status')
    is_verified = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    member_since = serializers.SerializerMethodField()

    def get_user_id(self, obj):
        return str(obj.profile.user_id)

    def get_full_name(self, obj):
        return _public_display_name(obj.profile)

    def get_avatar(self, obj):
        return _absolute_avatar(self.context.get('request'), obj.profile)

    def get_location(self, obj):
        return obj.profile.location or ''

    def get_headline_skills(self, obj):
        skills = list(obj.skills.all()[:5])
        return [{'id': str(s.id), 'name': s.name} for s in skills]

    def get_hourly_rate(self, obj):
        return str(obj.hourly_rate) if obj.hourly_rate is not None else None

    def get_is_verified(self, obj):
        return bool(obj.profile.is_verified)

    def get_rating(self, obj):
        count = getattr(obj, 'rating_count', None)
        return _provider_rating_payload(obj, rating_count=count)

    def get_member_since(self, obj):
        return obj.profile.created_at


class PublicProviderDetailSerializer(PublicProviderListSerializer):
    """Public provider profile detail — extends list card with bio/skills/experience."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['bio'] = instance.profile.bio or ''
        data['years_of_experience'] = instance.years_of_experience
        data['total_jobs_completed'] = instance.total_jobs_completed
        data['skills'] = TagSerializer(instance.skills.all(), many=True).data
        data['certifications'] = TagSerializer(instance.certifications.all(), many=True).data
        data['languages'] = TagSerializer(instance.languages.all(), many=True).data
        data['experiences'] = ExperienceSerializer(instance.experiences.all(), many=True).data
        return data
