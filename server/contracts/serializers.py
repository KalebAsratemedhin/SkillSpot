from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Contract, ContractMilestone, ContractSignature
from jobs.models import Job, JobApplication

User = get_user_model()


class ContractMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractMilestone
        fields = (
            'id', 'contract', 'title', 'description', 'amount',
            'due_date', 'status', 'order', 'completed_at',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'contract', 'completed_at', 'created_at', 'updated_at')

    def validate(self, attrs):
        contract = self.instance.contract if self.instance else self.context.get('contract')
        if contract:
            # Ensure milestone amount doesn't exceed remaining contract amount
            total_milestone_amount = sum(
                m.amount for m in contract.milestones.exclude(id=self.instance.id if self.instance else None)
            )
            new_amount = attrs.get('amount', self.instance.amount if self.instance else 0)
            if total_milestone_amount + new_amount > contract.total_amount:
                raise serializers.ValidationError({
                    'amount': 'Total milestone amounts cannot exceed contract total amount.'
                })
        return attrs


class ContractSignatureSerializer(serializers.ModelSerializer):
    signer_email = serializers.EmailField(source='signer.email', read_only=True)
    signer_name = serializers.SerializerMethodField()

    class Meta:
        model = ContractSignature
        fields = (
            'id', 'contract', 'signer', 'signer_email', 'signer_name',
            'is_signed', 'signature_data', 'signature_type',
            'ip_address', 'user_agent', 'signed_at',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'signer', 'signer_email', 'signer_name',
            'ip_address', 'user_agent', 'signed_at',
            'created_at', 'updated_at'
        )

    def get_signer_name(self, obj):
        if hasattr(obj.signer, 'profile') and obj.signer.profile:
            return obj.signer.profile.full_name
        return obj.signer.email


class ContractSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.email', read_only=True)
    client_name = serializers.SerializerMethodField()
    provider_email = serializers.EmailField(source='provider.email', read_only=True)
    provider_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True, allow_null=True)
    milestones = ContractMilestoneSerializer(many=True, read_only=True)
    signatures = ContractSignatureSerializer(many=True, read_only=True)
    is_fully_signed = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = (
            'id', 'job', 'job_title', 'job_application', 'client', 'client_email',
            'client_name', 'provider', 'provider_email', 'provider_name',
            'title', 'description', 'terms', 'total_amount', 'currency',
            'start_date', 'end_date', 'status', 'milestones', 'signatures',
            'is_fully_signed', 'completion_percentage',
            'created_at', 'updated_at', 'signed_at', 'completed_at'
        )
        read_only_fields = (
            'id', 'client', 'provider', 'signed_at', 'completed_at',
            'created_at', 'updated_at'
        )

    def get_client_name(self, obj):
        if hasattr(obj.client, 'profile') and obj.client.profile:
            return obj.client.profile.full_name
        return obj.client.email

    def get_provider_name(self, obj):
        if hasattr(obj.provider, 'profile') and obj.provider.profile:
            return obj.provider.profile.full_name
        return obj.provider.email

    def get_is_fully_signed(self, obj):
        return obj.is_fully_signed()

    def get_completion_percentage(self, obj):
        total_milestones = obj.milestones.count()
        if total_milestones == 0:
            return 0
        completed_milestones = obj.milestones.filter(
            status=ContractMilestone.MilestoneStatus.COMPLETED
        ).count()
        return int((completed_milestones / total_milestones) * 100)


class ContractCreateSerializer(serializers.ModelSerializer):
    milestones = ContractMilestoneSerializer(many=True, required=False)
    provider_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = Contract
        fields = (
            'job', 'job_application', 'provider_id', 'title', 'description',
            'terms', 'total_amount', 'currency', 'start_date', 'end_date',
            'milestones'
        )

    def validate(self, attrs):
        client = self.context['client']
        provider_id = attrs.get('provider_id')
        
        try:
            provider = User.objects.get(id=provider_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'provider_id': 'Provider not found.'
            })

        if provider.user_type not in ['PROVIDER', 'BOTH']:
            raise serializers.ValidationError({
                'provider_id': 'User must be a service provider.'
            })

        if client == provider:
            raise serializers.ValidationError({
                'provider_id': 'Client and provider cannot be the same user.'
            })

        # Validate job and job_application if provided
        job = attrs.get('job')
        job_application = attrs.get('job_application')

        if job and job.client != client:
            raise serializers.ValidationError({
                'job': 'You can only create contracts for your own jobs.'
            })

        if job_application:
            if job_application.job.client != client:
                raise serializers.ValidationError({
                    'job_application': 'You can only create contracts from your job applications.'
                })
            if job_application.provider != provider:
                raise serializers.ValidationError({
                    'provider_id': 'Provider must match the job application provider.'
                })

        # Validate milestones
        milestones_data = attrs.get('milestones', [])
        total_milestone_amount = sum(m.get('amount', 0) for m in milestones_data)
        if total_milestone_amount > attrs.get('total_amount', 0):
            raise serializers.ValidationError({
                'milestones': 'Total milestone amounts cannot exceed contract total amount.'
            })

        return attrs

    def create(self, validated_data):
        milestones_data = validated_data.pop('milestones', [])
        provider_id = validated_data.pop('provider_id')
        provider = User.objects.get(id=provider_id)
        client = self.context['client']

        contract = Contract.objects.create(
            client=client,
            provider=provider,
            **validated_data
        )

        # Create milestones
        for order, milestone_data in enumerate(milestones_data, start=1):
            ContractMilestone.objects.create(
                contract=contract,
                order=order,
                **milestone_data
            )

        # Create signature records for both parties
        ContractSignature.objects.create(
            contract=contract,
            signer=client
        )
        ContractSignature.objects.create(
            contract=contract,
            signer=provider
        )

        return contract


class ContractUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contract
        fields = (
            'title', 'description', 'terms', 'total_amount', 'currency',
            'start_date', 'end_date', 'status'
        )

    def validate(self, attrs):
        # Don't allow status changes to ACTIVE if not fully signed
        if 'status' in attrs:
            contract = self.instance
            if attrs['status'] == Contract.ContractStatus.ACTIVE:
                if not contract.is_fully_signed():
                    raise serializers.ValidationError({
                        'status': 'Contract must be fully signed before it can be activated.'
                    })
        return attrs


class ContractSignatureCreateSerializer(serializers.Serializer):
    signature_data = serializers.CharField(required=True)
    signature_type = serializers.ChoiceField(
        choices=['DIGITAL', 'IMAGE', 'TEXT'],
        default='DIGITAL'
    )

    def validate(self, attrs):
        contract = self.context['contract']
        signer = self.context['signer']

        # Verify signer is either client or provider
        if signer not in [contract.client, contract.provider]:
            raise serializers.ValidationError(
                'You are not authorized to sign this contract.'
            )

        # Check if already signed
        signature, created = ContractSignature.objects.get_or_create(
            contract=contract,
            signer=signer
        )
        if signature.is_signed:
            raise serializers.ValidationError(
                'You have already signed this contract.'
            )

        return attrs

    def save(self):
        contract = self.context['contract']
        signer = self.context['signer']
        request = self.context.get('request')

        signature, _ = ContractSignature.objects.get_or_create(
            contract=contract,
            signer=signer
        )

        signature.is_signed = True
        signature.signature_data = self.validated_data['signature_data']
        signature.signature_type = self.validated_data['signature_type']
        signature.signed_at = timezone.now()

        if request:
            signature.ip_address = self._get_client_ip(request)
            signature.user_agent = request.META.get('HTTP_USER_AGENT', '')

        signature.save()

        # Update contract status if both parties have signed
        if contract.is_fully_signed():
            contract.status = Contract.ContractStatus.PENDING_SIGNATURES
            contract.signed_at = timezone.now()
            contract.save()

        return signature

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
