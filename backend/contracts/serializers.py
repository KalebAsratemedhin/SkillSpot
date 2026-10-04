from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone
from .models import Contract, ContractMilestone, ContractSignature, TimeEntry
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


class TimeEntrySerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField()

    class Meta:
        model = TimeEntry
        fields = (
            'id', 'contract', 'provider', 'date', 'hours', 'description',
            'status', 'approved_by', 'approved_at', 'amount',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'contract', 'provider', 'approved_by', 'approved_at', 'created_at', 'updated_at')

    def get_amount(self, obj):
        amt = obj.amount  # model property: hours * contract.hourly_rate
        return amt if amt is not None else None


class TimeEntryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeEntry
        fields = ('date', 'hours', 'description')

    def validate_date(self, value):
        today = timezone.localdate()
        if value < today:
            raise serializers.ValidationError('Time entry date must be today or a future date.')
        return value

    def validate_hours(self, value):
        if value <= 0:
            raise serializers.ValidationError('Hours must be greater than zero.')
        return value


class TimeEntryApproveSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['APPROVED', 'REJECTED'])


class ContractSerializer(serializers.ModelSerializer):
    client_email = serializers.EmailField(source='client.email', read_only=True)
    client_name = serializers.SerializerMethodField()
    provider_email = serializers.EmailField(source='provider.email', read_only=True)
    provider_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True, allow_null=True)
    milestones = ContractMilestoneSerializer(many=True, read_only=True)
    time_entries = TimeEntrySerializer(many=True, read_only=True)
    signatures = ContractSignatureSerializer(many=True, read_only=True)
    is_fully_signed = serializers.SerializerMethodField()
    completion_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Contract
        fields = (
            'id', 'job', 'job_title', 'job_application', 'client', 'client_email',
            'client_name', 'provider', 'provider_email', 'provider_name',
            'title', 'description', 'terms', 'total_amount', 'currency',
            'payment_schedule', 'hourly_rate',
            'start_date', 'end_date', 'status', 'milestones', 'time_entries', 'signatures',
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
        from decimal import Decimal
        if obj.payment_schedule == Contract.PaymentSchedule.FIXED:
            # Fixed: 100% when full amount has been paid (one completed payment)
            paid = obj.payments.filter(status='COMPLETED').aggregate(
                total=Sum('amount')
            )['total'] or Decimal('0')
            if paid >= obj.total_amount:
                return 100
            return 0
        # Hourly: percentage = (sum of paid time entry amounts) / total_amount * 100
        paid_sum = obj.time_entries.filter(
            status=TimeEntry.TimeEntryStatus.PAID
        ).aggregate(
            total=Sum('hours')
        )['total']
        if paid_sum is None or obj.hourly_rate is None or obj.total_amount == 0:
            return 0
        amount_paid = paid_sum * obj.hourly_rate
        pct = int((amount_paid / obj.total_amount) * 100)
        return min(100, pct)


class ContractCreateSerializer(serializers.ModelSerializer):
    provider_id = serializers.UUIDField(write_only=True)
    payment_schedule = serializers.ChoiceField(
        choices=Contract.PaymentSchedule.choices,
        default=Contract.PaymentSchedule.FIXED,
    )
    hourly_rate = serializers.DecimalField(
        max_digits=10, decimal_places=2, required=False, allow_null=True,
        min_value=0,
    )

    class Meta:
        model = Contract
        fields = (
            'job', 'job_application', 'provider_id', 'title', 'description',
            'terms', 'total_amount', 'currency', 'payment_schedule', 'hourly_rate',
            'start_date', 'end_date',
        )

    def validate(self, attrs):
        client = self.context['client']
        provider_id = attrs.get('provider_id')
        payment_schedule = attrs.get('payment_schedule', Contract.PaymentSchedule.FIXED)
        hourly_rate = attrs.get('hourly_rate')

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
            # One contract per application
            if Contract.objects.filter(job_application=job_application).exists():
                raise serializers.ValidationError({
                    'job_application': 'A contract already exists for this application.'
                })
        elif job:
            # From invitation: one contract per job+provider (no application)
            if Contract.objects.filter(job=job, provider=provider, job_application__isnull=True).exists():
                raise serializers.ValidationError({
                    'job': 'A contract already exists for this job and provider (from invitation).'
                })

        # Payment schedule: HOURLY requires hourly_rate
        if payment_schedule == Contract.PaymentSchedule.HOURLY:
            if hourly_rate is None or hourly_rate <= 0:
                raise serializers.ValidationError({
                    'hourly_rate': 'Hourly rate is required and must be positive for hourly contracts.'
                })
        else:
            attrs['hourly_rate'] = None  # FIXED contracts don't use hourly_rate

        return attrs

    def create(self, validated_data):
        provider_id = validated_data.pop('provider_id')
        provider = User.objects.get(id=provider_id)
        client = self.context['client']

        contract = Contract.objects.create(
            client=client,
            provider=provider,
            **validated_data
        )

        # Create signature records for both parties (no milestones)
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
        if 'status' not in attrs:
            return attrs
        contract = self.instance
        new_status = attrs['status']
        # Don't allow status changes to ACTIVE if not fully signed
        if new_status == Contract.ContractStatus.ACTIVE:
            if not contract.is_fully_signed():
                raise serializers.ValidationError({
                    'status': 'Contract must be fully signed before it can be activated.'
                })
            return attrs
        # Allow ending contract: ACTIVE -> TERMINATED or COMPLETED
        if new_status in (Contract.ContractStatus.TERMINATED, Contract.ContractStatus.COMPLETED):
            if contract.status != Contract.ContractStatus.ACTIVE:
                raise serializers.ValidationError({
                    'status': 'Only active contracts can be ended.'
                })
        return attrs

    def update(self, instance, validated_data):
        new_status = validated_data.get('status')
        if new_status in (Contract.ContractStatus.TERMINATED, Contract.ContractStatus.COMPLETED):
            validated_data['completed_at'] = timezone.now()
        return super().update(instance, validated_data)


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

        # Re-fetch contract to avoid stale related data, then update status if both parties have signed
        contract.refresh_from_db()
        if contract.is_fully_signed():
            contract.status = Contract.ContractStatus.ACTIVE
            contract.signed_at = timezone.now()
            contract.save(update_fields=['status', 'signed_at', 'updated_at'])
            if contract.job_id:
                contract.job.status = Job.JobStatus.IN_PROGRESS
                contract.job.save(update_fields=['status'])

        return signature

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
