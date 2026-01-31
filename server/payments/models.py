import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from contracts.models import Contract, ContractMilestone

User = get_user_model()


class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        PROCESSING = 'PROCESSING', _('Processing')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
        REFUNDED = 'REFUNDED', _('Refunded')
        CANCELLED = 'CANCELLED', _('Cancelled')

    class PaymentMethod(models.TextChoices):
        STRIPE = 'STRIPE', _('Stripe')
        BANK_TRANSFER = 'BANK_TRANSFER', _('Bank Transfer')
        OTHER = 'OTHER', _('Other')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text=_('The contract this payment is associated with')
    )
    milestone = models.ForeignKey(
        ContractMilestone,
        on_delete=models.SET_NULL,
        related_name='payments',
        null=True,
        blank=True,
        help_text=_('Optional: Link to a specific milestone')
    )
    payer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments_made',
        help_text=_('User making the payment (typically the client)')
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='payments_received',
        help_text=_('User receiving the payment (typically the provider)')
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Payment amount')
    )
    currency = models.CharField(
        max_length=3,
        default='ETB',
        help_text=_('Currency code')
    )
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
        help_text=_('Current payment status')
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.STRIPE,
        help_text=_('Payment method used')
    )
    
    # Stripe-specific fields
    stripe_payment_intent_id = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Stripe PaymentIntent ID')
    )
    stripe_charge_id = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Stripe Charge ID')
    )
    stripe_refund_id = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Stripe Refund ID if refunded')
    )
    stripe_transfer_id = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Stripe Transfer ID to provider account')
    )
    platform_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Platform fee amount (if applicable)')
    )
    provider_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Amount transferred to provider (after platform fee)')
    )
    
    # Transaction details
    description = models.TextField(
        blank=True,
        help_text=_('Payment description')
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Additional metadata stored as JSON')
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp when payment was completed')
    )
    failed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp when payment failed')
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['payer', '-created_at']),
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['stripe_payment_intent_id']),
        ]

    def __str__(self):
        return f"{self.amount} {self.currency} - {self.payer.email} -> {self.recipient.email} ({self.status})"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Verify payer and recipient are different
        if self.payer == self.recipient:
            raise ValidationError('Payer and recipient cannot be the same user.')
        # Verify payer is the client and recipient is the provider
        if self.contract:
            if self.payer != self.contract.client:
                raise ValidationError('Payer must be the contract client.')
            if self.recipient != self.contract.provider:
                raise ValidationError('Recipient must be the contract provider.')


class PaymentTransaction(models.Model):
    """
    Track individual transaction events for a payment (for audit trail)
    """
    class TransactionType(models.TextChoices):
        CREATED = 'CREATED', _('Created')
        PROCESSING = 'PROCESSING', _('Processing')
        COMPLETED = 'COMPLETED', _('Completed')
        FAILED = 'FAILED', _('Failed')
        REFUNDED = 'REFUNDED', _('Refunded')
        CANCELLED = 'CANCELLED', _('Cancelled')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='transactions',
        help_text=_('The payment this transaction belongs to')
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        help_text=_('Type of transaction event')
    )
    stripe_event_id = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Stripe webhook event ID if applicable')
    )
    details = models.JSONField(
        default=dict,
        blank=True,
        help_text=_('Transaction details stored as JSON')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['payment', '-created_at']),
            models.Index(fields=['stripe_event_id']),
        ]

    def __str__(self):
        return f"{self.payment.id} - {self.transaction_type}"
