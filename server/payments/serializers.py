from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Payment, PaymentTransaction
from contracts.models import Contract, ContractMilestone

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
    transactions = PaymentTransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = (
            'id', 'contract', 'contract_title', 'milestone', 'milestone_title',
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

    class Meta:
        model = Payment
        fields = (
            'contract', 'milestone_id', 'amount', 'currency',
            'description', 'payment_method'
        )

    def validate(self, attrs):
        contract = attrs.get('contract')
        milestone_id = attrs.get('milestone_id')
        amount = attrs.get('amount')
        payer = self.context['payer']

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

        # Validate milestone if provided
        if milestone_id:
            try:
                milestone = ContractMilestone.objects.get(
                    id=milestone_id,
                    contract=contract
                )
                # Verify amount matches milestone amount
                if amount != milestone.amount:
                    raise serializers.ValidationError({
                        'amount': f'Amount must match milestone amount: {milestone.amount}'
                    })
                # Verify milestone hasn't been paid already
                if milestone.payments.filter(status=Payment.PaymentStatus.COMPLETED).exists():
                    raise serializers.ValidationError({
                        'milestone_id': 'This milestone has already been paid.'
                    })
            except ContractMilestone.DoesNotExist:
                raise serializers.ValidationError({
                    'milestone_id': 'Milestone not found or does not belong to this contract.'
                })

        # Verify amount is positive
        if amount <= 0:
            raise serializers.ValidationError({
                'amount': 'Payment amount must be greater than zero.'
            })

        return attrs

    def create(self, validated_data):
        milestone_id = validated_data.pop('milestone_id', None)
        contract = validated_data['contract']
        payer = self.context['payer']

        milestone = None
        if milestone_id:
            milestone = ContractMilestone.objects.get(id=milestone_id)

        payment = Payment.objects.create(
            contract=contract,
            milestone=milestone,
            payer=payer,
            recipient=contract.provider,
            **validated_data
        )

        # Create initial transaction record
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


class StripeWebhookSerializer(serializers.Serializer):
    """
    Serializer for handling Stripe webhook events
    """
    id = serializers.CharField()
    type = serializers.CharField()
    data = serializers.DictField()
