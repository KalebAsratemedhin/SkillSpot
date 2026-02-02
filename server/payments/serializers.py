from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Payment, PaymentTransaction
from contracts.models import Contract, ContractMilestone, TimeEntry

User = get_user_model()


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = (
            'id', 'payment', 'transaction_type', 'stripe_event_id',
            'details', 'created_at'
        )
        read_only_fields = ('id', 'payment', 'created_at')


class PaymentSerializer(serializers.ModelSerializer):
    payer_email = serializers.EmailField(source='payer.email', read_only=True)
    payer_name = serializers.SerializerMethodField()
    recipient_email = serializers.EmailField(source='recipient.email', read_only=True)
    recipient_name = serializers.SerializerMethodField()
    contract_title = serializers.CharField(source='contract.title', read_only=True)
    milestone_title = serializers.CharField(source='milestone.title', read_only=True, allow_null=True)
    time_entry_id = serializers.UUIDField(source='time_entry.id', read_only=True, allow_null=True)
    transactions = PaymentTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'contract', 'contract_title', 'milestone', 'milestone_title',
            'time_entry', 'time_entry_id',
            'payer', 'payer_email', 'payer_name', 'recipient', 'recipient_email',
            'recipient_name', 'amount', 'currency', 'status', 'payment_method',
            'stripe_payment_intent_id', 'stripe_charge_id', 'stripe_refund_id',
            'description', 'metadata', 'transactions',
            'created_at', 'updated_at', 'completed_at', 'failed_at'
        )
        read_only_fields = (
            'id', 'payer', 'recipient', 'status', 'stripe_payment_intent_id',
            'stripe_charge_id', 'stripe_refund_id', 'created_at', 'updated_at',
            'completed_at', 'failed_at'
        )

    def get_payer_name(self, obj):
        if hasattr(obj.payer, 'profile') and obj.payer.profile:
            return obj.payer.profile.full_name
        return obj.payer.email

    def get_recipient_name(self, obj):
        if hasattr(obj.recipient, 'profile') and obj.recipient.profile:
            return obj.recipient.profile.full_name
        return obj.recipient.email


class PaymentCreateSerializer(serializers.ModelSerializer):
    milestone_id = serializers.UUIDField(required=False, allow_null=True)
    time_entry_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'contract', 'milestone_id', 'time_entry_id', 'amount', 'currency',
            'description', 'payment_method'
        )
        read_only_fields = ('id',)

    def validate(self, attrs):
        contract = attrs.get('contract')
        milestone_id = attrs.get('milestone_id')
        time_entry_id = attrs.get('time_entry_id')
        amount = attrs.get('amount')
        
        # Get payer from context (set by view's get_serializer_context)
        payer = self.context.get('payer')
        if not payer:
            raise serializers.ValidationError('Authentication required to create payment.')

        # Verify payer is the contract client
        if contract.client != payer:
            raise serializers.ValidationError({
                'contract': 'You can only make payments for your own contracts.'
            })

        # Verify contract is active
        if contract.status != Contract.ContractStatus.ACTIVE:
            raise serializers.ValidationError({
                'contract': 'Payments can only be made for active contracts.'
            })

        # Fixed price: amount must equal total_amount, no time_entry; one full payment only
        if contract.payment_schedule == Contract.PaymentSchedule.FIXED:
            if time_entry_id:
                raise serializers.ValidationError({
                    'time_entry_id': 'Time entry is only for hourly contracts.'
                })
            if amount != contract.total_amount:
                raise serializers.ValidationError({
                    'amount': f'Fixed price payment must equal contract total: {contract.total_amount}'
                })
            if contract.payments.filter(status=Payment.PaymentStatus.COMPLETED).exists():
                raise serializers.ValidationError({
                    'contract': 'This fixed-price contract has already been paid in full.'
                })
            attrs['time_entry'] = None
            attrs['milestone'] = None
            return attrs

        # Hourly: time_entry_id required, amount from time_entry
        if contract.payment_schedule == Contract.PaymentSchedule.HOURLY:
            if not time_entry_id:
                raise serializers.ValidationError({
                    'time_entry_id': 'Time entry is required for hourly contract payments.'
                })
            try:
                time_entry = TimeEntry.objects.get(
                    id=time_entry_id,
                    contract=contract
                )
            except TimeEntry.DoesNotExist:
                raise serializers.ValidationError({
                    'time_entry_id': 'Time entry not found or does not belong to this contract.'
                })
            if time_entry.status != TimeEntry.TimeEntryStatus.APPROVED:
                raise serializers.ValidationError({
                    'time_entry_id': 'Only approved time entries can be paid.'
                })
            if time_entry.payments.filter(status=Payment.PaymentStatus.COMPLETED).exists():
                raise serializers.ValidationError({
                    'time_entry_id': 'This time entry has already been paid.'
                })
            expected_amount = time_entry.amount
            if expected_amount is None:
                raise serializers.ValidationError({
                    'time_entry_id': 'Time entry amount could not be calculated (missing hourly rate).'
                })
            if amount != expected_amount:
                raise serializers.ValidationError({
                    'amount': f'Amount must match time entry total: {expected_amount}'
                })
            attrs['time_entry'] = time_entry
            attrs['milestone'] = None
            return attrs

        # Legacy: milestone_id (contracts without payment_schedule or old milestone-based)
        if milestone_id:
            try:
                milestone = ContractMilestone.objects.get(
                    id=milestone_id,
                    contract=contract
                )
                if amount != milestone.amount:
                    raise serializers.ValidationError({
                        'amount': f'Amount must match milestone amount: {milestone.amount}'
                    })
                if milestone.payments.filter(status=Payment.PaymentStatus.COMPLETED).exists():
                    raise serializers.ValidationError({
                        'milestone_id': 'This milestone has already been paid.'
                    })
                attrs['milestone'] = milestone
                attrs['time_entry'] = None
            except ContractMilestone.DoesNotExist:
                raise serializers.ValidationError({
                    'milestone_id': 'Milestone not found or does not belong to this contract.'
                })
        else:
            raise serializers.ValidationError({
                'contract': 'Fixed and hourly contracts require amount or time_entry_id respectively.'
            })

        if amount <= 0:
            raise serializers.ValidationError({
                'amount': 'Payment amount must be greater than zero.'
            })
        return attrs

    def create(self, validated_data):
        milestone_id = validated_data.pop('milestone_id', None)
        time_entry_id = validated_data.pop('time_entry_id', None)
        time_entry = validated_data.pop('time_entry', None)
        milestone = validated_data.pop('milestone', None)
        contract = validated_data.pop('contract')
        payer = self.context.get('payer')

        if milestone_id and not milestone:
            milestone = ContractMilestone.objects.get(id=milestone_id)

        payment = Payment.objects.create(
            contract=contract,
            milestone=milestone,
            time_entry=time_entry,
            payer=payer,
            recipient=contract.provider,
            **validated_data
        )

        PaymentTransaction.objects.create(
            payment=payment,
            transaction_type=PaymentTransaction.TransactionType.CREATED,
            details={'created_by': str(payer.id)}
        )

        return payment


class StripePaymentIntentSerializer(serializers.Serializer):
    """
    Serializer for creating a Stripe PaymentIntent
    """
    payment_id = serializers.UUIDField(required=True)
    return_url = serializers.URLField(required=False, allow_blank=True)

    def validate_payment_id(self, value):
        try:
            payment = Payment.objects.get(id=value)
            if payment.status != Payment.PaymentStatus.PENDING:
                raise serializers.ValidationError(
                    'Payment is not in pending status.'
                )
            if payment.payment_method != Payment.PaymentMethod.STRIPE:
                raise serializers.ValidationError(
                    'Payment method is not Stripe.'
                )
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError('Payment not found.')


class StripeCheckoutSessionSerializer(serializers.Serializer):
    """
    Serializer for creating a Stripe Checkout Session (pay on Stripe's hosted page, on behalf of connected provider).
    """
    payment_id = serializers.UUIDField(required=True)
    success_url = serializers.URLField(required=False, allow_blank=True)
    cancel_url = serializers.URLField(required=False, allow_blank=True)

    def validate_payment_id(self, value):
        try:
            payment = Payment.objects.get(id=value)
            if payment.status != Payment.PaymentStatus.PENDING:
                raise serializers.ValidationError(
                    'Payment is not in pending status.'
                )
            if payment.payment_method != Payment.PaymentMethod.STRIPE:
                raise serializers.ValidationError(
                    'Payment method is not Stripe.'
                )
            return value
        except Payment.DoesNotExist:
            raise serializers.ValidationError('Payment not found.')


class StripeWebhookSerializer(serializers.Serializer):
    """
    Serializer for handling Stripe webhook events
    """
    id = serializers.CharField()
    type = serializers.CharField()
    data = serializers.DictField()
