from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Job, JobApplication, JobInvitation
from profiles.models import Tag
from profiles.serializers import TagSerializer
from ratings.models import Rating

User = get_user_model()


class JobSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.email', read_only=True)
    client_name = serializers.SerializerMethodField()
    client_profile = serializers.SerializerMethodField()
    client_rating = serializers.SerializerMethodField()
    my_application = serializers.SerializerMethodField()
    required_skills = TagSerializer(many=True, read_only=True)
    skill_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.filter(category=Tag.TagCategory.SKILL),
        write_only=True,
        required=False,
        source='required_skills'
    )
    applications_count = serializers.SerializerMethodField()
    accepted_applications_count = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = (
            'id', 'client', 'client_email', 'client_name', 'client_profile',
            'client_rating', 'my_application', 'title', 'description',
            'budget_min', 'budget_max', 'currency', 'location',
            'address', 'latitude', 'longitude', 'is_remote', 'status',
            'payment_schedule', 'required_skills', 'skill_ids',
            'deadline', 'applications_count', 'accepted_applications_count',
            'created_at', 'updated_at', 'closed_at'
        )
        read_only_fields = (
            'id', 'client', 'client_profile', 'client_rating', 'my_application',
            'created_at', 'updated_at', 'closed_at',
        )

    def get_client_name(self, obj):
        if hasattr(obj.client, 'profile') and obj.client.profile:
            return obj.client.profile.full_name
        return obj.client.email

    def get_client_profile(self, obj):
        client = obj.client
        profile = getattr(client, 'profile', None)
        request = self.context.get('request')
        authenticated = bool(
            request and getattr(request.user, 'is_authenticated', False)
        )
        avatar = None
        location = ''
        member_since = client.date_joined
        # Never fall back to email for public display names
        full_name = ''

        if profile is not None:
            if profile.first_name or profile.last_name:
                full_name = f'{profile.first_name} {profile.last_name}'.strip()
            location = profile.location or ''
            member_since = profile.created_at
            if profile.avatar:
                if request:
                    avatar = request.build_absolute_uri(profile.avatar.url)
                else:
                    avatar = profile.avatar.url

        if not full_name and authenticated:
            full_name = client.email

        data = {
            'id': str(client.id),
            'full_name': full_name,
            'avatar': avatar,
            'location': location,
            'member_since': member_since,
        }
        # Email only for authenticated viewers (private)
        data['email'] = client.email if authenticated else None
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        authenticated = bool(
            request and getattr(request.user, 'is_authenticated', False)
        )
        if not authenticated:
            data['client_email'] = None
            # Prefer non-email client_name for guests
            profile = getattr(instance.client, 'profile', None)
            if profile and (profile.first_name or profile.last_name):
                data['client_name'] = f'{profile.first_name} {profile.last_name}'.strip()
            else:
                data['client_name'] = data.get('client_profile', {}).get('full_name') or ''
        return data

    def get_client_rating(self, obj):
        stats = Rating.calculate_average_rating(
            obj.client,
            rating_type=Rating.RatingType.PROVIDER_TO_CLIENT,
        )
        count = stats['count'] or 0
        if count == 0:
            return {'average': None, 'count': 0}
        return {'average': stats['average'], 'count': count}

    def get_my_application(self, obj):
        request = self.context.get('request')
        if not request or not getattr(request.user, 'is_authenticated', False):
            return None

        user = request.user
        if obj.client_id == user.id:
            return None
        if user.user_type not in ['PROVIDER', 'BOTH']:
            return None

        apps = getattr(obj, '_my_applications', None)
        if apps is not None:
            application = apps[0] if apps else None
        else:
            prefetched = getattr(obj, '_prefetched_objects_cache', {}).get('applications')
            if prefetched is not None:
                application = next((a for a in prefetched if a.provider_id == user.id), None)
            else:
                application = obj.applications.filter(provider=user).first()

        if application is None:
            return None

        return {
            'id': str(application.id),
            'status': application.status,
            'cover_letter': application.cover_letter or '',
            'proposed_rate': (
                str(application.proposed_rate)
                if application.proposed_rate is not None
                else None
            ),
            'applied_at': application.applied_at,
        }

    def get_applications_count(self, obj):
        return obj.applications.count()

    def get_accepted_applications_count(self, obj):
        return obj.applications.filter(status=JobApplication.ApplicationStatus.ACCEPTED).count()


class JobCreateSerializer(serializers.ModelSerializer):
    skill_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.filter(category=Tag.TagCategory.SKILL),
        required=False,
        source='required_skills'
    )
    location = serializers.CharField(required=False, allow_blank=True, default='')
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )

    class Meta:
        model = Job
        fields = (
            'id', 'title', 'description', 'budget_min', 'budget_max',
            'currency', 'location', 'address', 'is_remote', 'status',
            'payment_schedule', 'required_skills', 'skill_ids', 'deadline',
            'latitude', 'longitude',
        )
        read_only_fields = ('id',)

    def validate(self, attrs):
        budget_min = attrs.get('budget_min')
        budget_max = attrs.get('budget_max')

        if budget_min and budget_max and budget_min > budget_max:
            raise serializers.ValidationError({
                'budget_max': 'Maximum budget must be greater than or equal to minimum budget.'
            })

        return attrs


class JobApplicationSerializer(serializers.ModelSerializer):
    provider_email = serializers.EmailField(source='provider.email', read_only=True)
    provider_name = serializers.SerializerMethodField()
    provider_summary = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_client = serializers.UUIDField(source='job.client.id', read_only=True)

    class Meta:
        model = JobApplication
        fields = (
            'id', 'job', 'job_title', 'job_client', 'provider', 'provider_email',
            'provider_name', 'provider_summary', 'cover_letter', 'proposed_rate',
            'status', 'applied_at', 'reviewed_at'
        )
        read_only_fields = (
            'id', 'provider', 'provider_summary', 'status', 'applied_at', 'reviewed_at'
        )

    def get_provider_name(self, obj):
        profile = getattr(obj.provider, 'profile', None)
        if profile and (profile.first_name or profile.last_name):
            return f'{profile.first_name} {profile.last_name}'.strip()
        if profile:
            return profile.full_name
        return obj.provider.email

    def get_provider_summary(self, obj):
        provider = obj.provider
        profile = getattr(provider, 'profile', None)
        provider_profile = getattr(profile, 'provider_profile', None) if profile else None
        request = self.context.get('request')

        full_name = ''
        avatar = None
        location = ''
        hourly_rate = None
        is_verified = False
        rating_avg = None
        rating_count = 0

        if profile is not None:
            if profile.first_name or profile.last_name:
                full_name = f'{profile.first_name} {profile.last_name}'.strip()
            else:
                full_name = profile.full_name if profile.full_name != provider.email else ''
            location = profile.location or ''
            is_verified = bool(profile.is_verified)
            if profile.avatar:
                if request:
                    avatar = request.build_absolute_uri(profile.avatar.url)
                else:
                    avatar = profile.avatar.url

        if provider_profile is not None:
            hourly_rate = (
                str(provider_profile.hourly_rate)
                if provider_profile.hourly_rate is not None
                else None
            )
            avg = provider_profile.average_rating
            if avg is not None and float(avg) > 0:
                rating_avg = float(avg)
            stats = Rating.calculate_average_rating(
                provider,
                rating_type=Rating.RatingType.CLIENT_TO_PROVIDER,
            )
            rating_count = stats['count'] or 0
            if rating_count == 0:
                rating_avg = None
            elif rating_avg is None:
                rating_avg = stats['average']

        return {
            'user_id': str(provider.id),
            'full_name': full_name,
            'avatar': avatar,
            'location': location,
            'hourly_rate': hourly_rate,
            'is_verified': is_verified,
            'rating': {
                'average': rating_avg,
                'count': rating_count,
            },
        }


class JobApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ('cover_letter', 'proposed_rate')

    def validate(self, attrs):
        job = self.context['job']
        provider = self.context['provider']

        if JobApplication.objects.filter(job=job, provider=provider).exists():
            raise serializers.ValidationError('You have already applied to this job.')

        if JobInvitation.objects.filter(job=job, provider=provider).exists():
            raise serializers.ValidationError(
                'You have been invited to this job. Please check your invitations and accept or decline there instead of applying.'
            )

        if job.status != Job.JobStatus.OPEN:
            raise serializers.ValidationError('This job is not open for applications.')

        return attrs


class JobInvitationSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.email', read_only=True)
    client_name = serializers.SerializerMethodField()
    provider_email = serializers.EmailField(source='provider.email', read_only=True)
    provider_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True, allow_null=True)

    class Meta:
        model = JobInvitation
        fields = (
            'id', 'job', 'job_title', 'client', 'client_email', 'client_name',
            'provider', 'provider_email', 'provider_name', 'message', 'status',
            'invited_at', 'responded_at'
        )
        read_only_fields = ('id', 'client', 'status', 'invited_at', 'responded_at')

    def get_client_name(self, obj):
        if hasattr(obj.client, 'profile') and obj.client.profile:
            return obj.client.profile.full_name
        return obj.client.email

    def get_provider_name(self, obj):
        if hasattr(obj.provider, 'profile') and obj.provider.profile:
            return obj.provider.profile.full_name
        return obj.provider.email


class JobInvitationCreateSerializer(serializers.ModelSerializer):
    provider = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(user_type__in=['PROVIDER', 'BOTH']),
        required=False,
        allow_null=True
    )
    provider_email = serializers.EmailField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = JobInvitation
        fields = ('job', 'provider', 'provider_email', 'message')

    def validate(self, attrs):
        client = self.context['client']
        provider = attrs.get('provider')
        provider_email = (attrs.pop('provider_email', None) or '').strip()
        job = attrs.get('job')

        if provider_email and not provider:
            try:
                user = User.objects.get(email__iexact=provider_email)
                provider = user
                attrs['provider'] = provider
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'provider_email': 'No user found with this email.'
                })

        if not provider:
            raise serializers.ValidationError({
                'provider': 'Provider or provider_email is required.'
            })

        if provider.user_type not in ['PROVIDER', 'BOTH']:
            raise serializers.ValidationError({
                'provider': 'User must be a service provider.',
                'provider_email': 'This user is not registered as a provider.'
            })

        if job and job.client != client:
            raise serializers.ValidationError({
                'job': 'You can only invite providers to your own jobs.'
            })

        if JobInvitation.objects.filter(
            client=client,
            provider=provider,
            job=job if job else None,
            status=JobInvitation.InvitationStatus.PENDING
        ).exists():
            raise serializers.ValidationError({
                'provider_email': 'An invitation has already been sent to this provider for this job.'
            })

        return attrs
