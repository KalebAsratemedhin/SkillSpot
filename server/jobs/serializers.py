from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Job, JobApplication, JobInvitation
from profiles.models import Tag
from profiles.serializers import TagSerializer

User = get_user_model()


class JobSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.email', read_only=True)
    client_name = serializers.SerializerMethodField()
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
            'id', 'client', 'client_email', 'client_name', 'title', 'description',
            'job_type', 'budget_min', 'budget_max', 'currency', 'location',
            'address', 'is_remote', 'status', 'required_skills', 'skill_ids',
            'deadline', 'applications_count', 'accepted_applications_count',
            'created_at', 'updated_at', 'closed_at'
        )
        read_only_fields = ('id', 'client', 'created_at', 'updated_at', 'closed_at')

    def get_client_name(self, obj):
        if hasattr(obj.client, 'profile') and obj.client.profile:
            return obj.client.profile.full_name
        return obj.client.email

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

    class Meta:
        model = Job
        fields = (
            'title', 'description', 'job_type', 'budget_min', 'budget_max',
            'currency', 'location', 'address', 'is_remote', 'status',
            'required_skills', 'skill_ids', 'deadline'
        )

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
    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = JobApplication
        fields = (
            'id', 'job', 'job_title', 'provider', 'provider_email',
            'provider_name', 'cover_letter', 'proposed_rate', 'status',
            'applied_at', 'reviewed_at'
        )
        read_only_fields = ('id', 'provider', 'status', 'applied_at', 'reviewed_at')

    def get_provider_name(self, obj):
        if hasattr(obj.provider, 'profile') and obj.provider.profile:
            return obj.provider.profile.full_name
        return obj.provider.email


class JobApplicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobApplication
        fields = ('cover_letter', 'proposed_rate')

    def validate(self, attrs):
        job = self.context['job']
        provider = self.context['provider']
        
        if JobApplication.objects.filter(job=job, provider=provider).exists():
            raise serializers.ValidationError('You have already applied to this job.')
        
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
    class Meta:
        model = JobInvitation
        fields = ('job', 'provider', 'message')

    def validate(self, attrs):
        client = self.context['client']
        provider = attrs.get('provider')
        job = attrs.get('job')

        if provider and provider.user_type not in ['PROVIDER', 'BOTH']:
            raise serializers.ValidationError({
                'provider': 'User must be a service provider.'
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
            raise serializers.ValidationError('An invitation has already been sent.')

        return attrs
