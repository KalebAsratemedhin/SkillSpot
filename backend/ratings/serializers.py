from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Rating
from jobs.models import Job, JobApplication
from contracts.models import Contract

User = get_user_model()


class RatingSerializer(serializers.ModelSerializer):
    rater_email = serializers.EmailField(source='rater.email', read_only=True)
    rater_name = serializers.SerializerMethodField()
    rated_user_email = serializers.EmailField(source='rated_user.email', read_only=True)
    rated_user_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True, allow_null=True)
    contract_title = serializers.CharField(source='contract.title', read_only=True, allow_null=True)

    class Meta:
        model = Rating
        fields = (
            'id', 'job', 'job_title', 'contract', 'contract_title',
            'rater', 'rater_email', 'rater_name', 'rated_user', 'rated_user_email',
            'rated_user_name', 'rating_type', 'score', 'comment',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'rater', 'rater_email', 'rater_name', 'rated_user', 'rated_user_email',
            'rated_user_name', 'created_at', 'updated_at'
        )

    def get_rater_name(self, obj):
        if hasattr(obj.rater, 'profile') and obj.rater.profile:
            return obj.rater.profile.full_name
        return obj.rater.email

    def get_rated_user_name(self, obj):
        if hasattr(obj.rated_user, 'profile') and obj.rated_user.profile:
            return obj.rated_user.profile.full_name
        return obj.rated_user.email


class RatingCreateSerializer(serializers.ModelSerializer):
    job_id = serializers.UUIDField(required=False, allow_null=True)
    contract_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Rating
        fields = ('job_id', 'contract_id', 'score', 'comment', 'rating_type')

    def validate(self, attrs):
        rater = self.context['rater']
        job_id = attrs.get('job_id')
        contract_id = attrs.get('contract_id')
        rating_type = attrs.get('rating_type')

        # Ensure either job or contract is provided
        if not job_id and not contract_id:
            raise serializers.ValidationError({
                'job_id': 'Either job_id or contract_id must be provided.',
                'contract_id': 'Either job_id or contract_id must be provided.'
            })
        if job_id and contract_id:
            raise serializers.ValidationError({
                'job_id': 'Cannot provide both job_id and contract_id.',
                'contract_id': 'Cannot provide both job_id and contract_id.'
            })

        # Validate job
        if job_id:
            try:
                job = Job.objects.get(id=job_id)
            except Job.DoesNotExist:
                raise serializers.ValidationError({
                    'job_id': 'Job not found.'
                })

            # Verify job is completed
            if job.status != Job.JobStatus.COMPLETED:
                raise serializers.ValidationError({
                    'job_id': 'Can only rate completed jobs.'
                })

            # Validate rating type and rater
            if rating_type == Rating.RatingType.CLIENT_TO_PROVIDER:
                if rater != job.client:
                    raise serializers.ValidationError({
                        'rating_type': 'Only the client can rate the provider.'
                    })
                # Verify provider has accepted application or invitation
                has_accepted_application = JobApplication.objects.filter(
                    job=job,
                    status=JobApplication.ApplicationStatus.ACCEPTED,
                    provider__user_type__in=['PROVIDER', 'BOTH']
                ).exists()
                if not has_accepted_application:
                    raise serializers.ValidationError({
                        'job_id': 'No accepted provider found for this job.'
                    })
            elif rating_type == Rating.RatingType.PROVIDER_TO_CLIENT:
                if rater.user_type not in ['PROVIDER', 'BOTH']:
                    raise serializers.ValidationError({
                        'rating_type': 'Only providers can rate clients.'
                    })
                # Verify rater has accepted application
                has_accepted_application = JobApplication.objects.filter(
                    job=job,
                    provider=rater,
                    status=JobApplication.ApplicationStatus.ACCEPTED
                ).exists()
                if not has_accepted_application:
                    raise serializers.ValidationError({
                        'job_id': 'You must be the accepted provider for this job.'
                    })

        # Validate contract
        if contract_id:
            try:
                contract = Contract.objects.get(id=contract_id)
            except Contract.DoesNotExist:
                raise serializers.ValidationError({
                    'contract_id': 'Contract not found.'
                })

            # Verify contract is completed
            if contract.status != Contract.ContractStatus.COMPLETED:
                raise serializers.ValidationError({
                    'contract_id': 'Can only rate completed contracts.'
                })

            # Validate rating type and rater
            if rating_type == Rating.RatingType.CLIENT_TO_PROVIDER:
                if rater != contract.client:
                    raise serializers.ValidationError({
                        'rating_type': 'Only the client can rate the provider.'
                    })
            elif rating_type == Rating.RatingType.PROVIDER_TO_CLIENT:
                if rater != contract.provider:
                    raise serializers.ValidationError({
                        'rating_type': 'Only the provider can rate the client.'
                    })

        # Check if rating already exists
        existing_rating = Rating.objects.filter(
            rater=rater,
            rating_type=rating_type,
            **({'job_id': job_id} if job_id else {'contract_id': contract_id})
        ).first()

        if existing_rating:
            raise serializers.ValidationError({
                'rating_type': 'You have already rated this job/contract.'
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop('rater', None)  # use context rater only; view may pass rater in save()
        rater = self.context['rater']
        job_id = validated_data.pop('job_id', None)
        contract_id = validated_data.pop('contract_id', None)
        rating_type = validated_data['rating_type']

        job = None
        contract = None
        rated_user = None

        if job_id:
            job = Job.objects.get(id=job_id)
            if rating_type == Rating.RatingType.CLIENT_TO_PROVIDER:
                # Get the accepted provider
                application = JobApplication.objects.filter(
                    job=job,
                    status=JobApplication.ApplicationStatus.ACCEPTED
                ).first()
                if application:
                    rated_user = application.provider
            elif rating_type == Rating.RatingType.PROVIDER_TO_CLIENT:
                rated_user = job.client

        if contract_id:
            contract = Contract.objects.get(id=contract_id)
            if rating_type == Rating.RatingType.CLIENT_TO_PROVIDER:
                rated_user = contract.provider
            elif rating_type == Rating.RatingType.PROVIDER_TO_CLIENT:
                rated_user = contract.client

        if not rated_user:
            raise serializers.ValidationError({
                'rating_type': 'Could not determine rated user.'
            })

        rating = Rating.objects.create(
            job=job,
            contract=contract,
            rater=rater,
            rated_user=rated_user,
            **validated_data
        )

        return rating


class RatingUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = ('score', 'comment')

    def validate_score(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('Score must be between 1 and 5.')
        return value


class UserRatingStatsSerializer(serializers.Serializer):
    """
    Serializer for user rating statistics
    """
    user_id = serializers.UUIDField()
    user_email = serializers.EmailField()
    user_name = serializers.CharField()
    average_rating_as_provider = serializers.DecimalField(max_digits=3, decimal_places=2)
    rating_count_as_provider = serializers.IntegerField()
    average_rating_as_client = serializers.DecimalField(max_digits=3, decimal_places=2)
    rating_count_as_client = serializers.IntegerField()
    total_ratings = serializers.IntegerField()
