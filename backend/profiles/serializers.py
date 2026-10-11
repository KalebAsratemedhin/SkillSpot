from datetime import datetime, time

from django.contrib.auth import get_user_model
from django.db.models import Count, Prefetch, Q
from rest_framework import serializers

from contracts.models import Contract
from ratings.models import Rating
from .models import Profile, ServiceProviderProfile, Tag, Experience

User = get_user_model()

# Public provider work history: max items per bucket (counts are uncapped).
WORK_HISTORY_LIMIT = 20
PLATFORM_CURRENCY = 'USD'


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


def _contract_started_at(contract):
    """Prefer signed_at → start_date (UTC midnight) → created_at."""
    if contract.signed_at:
        return contract.signed_at
    if contract.start_date:
        from datetime import timezone as dt_timezone
        return datetime.combine(contract.start_date, time.min, tzinfo=dt_timezone.utc)
    return contract.created_at


def _work_item_review(contract):
    """CLIENT_TO_PROVIDER review for this contract, or None. No email/phone."""
    reviews = getattr(contract, 'client_to_provider_reviews', None)
    if reviews is None:
        reviews = list(
            contract.ratings.filter(
                rating_type=Rating.RatingType.CLIENT_TO_PROVIDER,
            ).select_related('rater__profile')[:1]
        )
    if not reviews:
        return None
    rating = reviews[0]
    rater_profile = getattr(rating.rater, 'profile', None)
    return {
        'id': str(rating.id),
        'score': rating.score,
        'comment': rating.comment or '',
        'rater_name': _public_display_name(rater_profile),
        'created_at': rating.created_at,
    }


def _serialize_work_item(contract, *, closed=False):
    job = contract.job
    job_title = (job.title if job and job.title else None) or contract.title
    return {
        'contract_id': str(contract.id),
        'job_id': str(job.id) if job else None,
        'job_title': job_title,
        'status': contract.status,
        'started_at': _contract_started_at(contract),
        'completed_at': contract.completed_at if closed else None,
        'amount': str(contract.total_amount),
        'currency': (contract.currency or PLATFORM_CURRENCY).upper(),
        'review': _work_item_review(contract) if closed else None,
    }


def _provider_work_history(user):
    """
    Build in_progress / closed WorkItems for a provider user.
    Counts are full; lists capped at WORK_HISTORY_LIMIT.
    """
    review_prefetch = Prefetch(
        'ratings',
        queryset=Rating.objects.filter(
            rating_type=Rating.RatingType.CLIENT_TO_PROVIDER,
        ).select_related('rater__profile').order_by('-created_at'),
        to_attr='client_to_provider_reviews',
    )
    base = (
        Contract.objects.filter(provider=user)
        .select_related('job')
        .prefetch_related(review_prefetch)
    )
    counts = base.aggregate(
        in_progress=Count(
            'id',
            filter=Q(status=Contract.ContractStatus.ACTIVE),
        ),
        closed=Count(
            'id',
            filter=Q(
                status__in=[
                    Contract.ContractStatus.COMPLETED,
                    Contract.ContractStatus.TERMINATED,
                ]
            ),
        ),
    )
    in_progress_qs = list(
        base.filter(status=Contract.ContractStatus.ACTIVE).order_by(
            '-signed_at', '-updated_at', '-created_at',
        )[:WORK_HISTORY_LIMIT]
    )
    in_progress_qs.sort(key=_contract_started_at, reverse=True)

    closed_qs = list(
        base.filter(
            status__in=[
                Contract.ContractStatus.COMPLETED,
                Contract.ContractStatus.TERMINATED,
            ]
        ).order_by('-completed_at', '-updated_at', '-created_at')[:WORK_HISTORY_LIMIT]
    )

    return {
        'jobs_in_progress_count': counts['in_progress'] or 0,
        'jobs_closed_count': counts['closed'] or 0,
        'work_history': {
            'in_progress': [
                _serialize_work_item(c, closed=False) for c in in_progress_qs
            ],
            'closed': [
                _serialize_work_item(c, closed=True) for c in closed_qs
            ],
        },
    }


class PublicProviderDetailSerializer(PublicProviderListSerializer):
    """Public provider profile detail — bio, skills, experience, work history, earnings."""

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['bio'] = instance.profile.bio or ''
        data['years_of_experience'] = instance.years_of_experience
        data['total_jobs_completed'] = instance.total_jobs_completed
        data['total_earnings'] = str(instance.total_earnings or 0)
        data['currency'] = PLATFORM_CURRENCY
        data['skills'] = TagSerializer(instance.skills.all(), many=True).data
        data['certifications'] = TagSerializer(instance.certifications.all(), many=True).data
        data['languages'] = TagSerializer(instance.languages.all(), many=True).data
        # Prefetch order follows Experience.Meta (-is_current, -start_date)
        data['experiences'] = ExperienceSerializer(
            instance.experiences.all(), many=True,
        ).data
        data.update(_provider_work_history(instance.profile.user))
        return data
