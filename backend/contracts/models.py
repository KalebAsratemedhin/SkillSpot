import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from jobs.models import Job, JobApplication

User = get_user_model()


class Contract(models.Model):
    class ContractStatus(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        PENDING_SIGNATURES = 'PENDING_SIGNATURES', _('Pending Signatures')
        ACTIVE = 'ACTIVE', _('Active')
        COMPLETED = 'COMPLETED', _('Completed')
        TERMINATED = 'TERMINATED', _('Terminated')
        CANCELLED = 'CANCELLED', _('Cancelled')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='contracts',
        null=True,
        blank=True,
        help_text=_('Optional: Link to a job if contract is created from a job')
    )
    job_application = models.ForeignKey(
        JobApplication,
        on_delete=models.SET_NULL,
        related_name='contracts',
        null=True,
        blank=True,
        help_text=_('Optional: Link to a job application if contract is created from an application')
    )
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_contracts',
        help_text=_('The client who is hiring')
    )
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='provider_contracts',
        help_text=_('The service provider')
    )
    title = models.CharField(
        max_length=200,
        help_text=_('Contract title')
    )
    description = models.TextField(
        help_text=_('Detailed contract description and terms')
    )
    terms = models.TextField(
        help_text=_('Contract terms and conditions')
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Total contract amount (fixed price) or cap (hourly)')
    )
    class PaymentSchedule(models.TextChoices):
        FIXED = 'FIXED', _('Fixed Price')
        HOURLY = 'HOURLY', _('Hourly')

    payment_schedule = models.CharField(
        max_length=20,
        choices=PaymentSchedule.choices,
        default=PaymentSchedule.FIXED,
        help_text=_('FIXED = pay once; HOURLY = provider logs hours, client approves and pays')
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Rate per hour (for HOURLY contracts only)')
    )
    currency = models.CharField(
        max_length=3,
        default='ETB',
        help_text=_('Currency code')
    )
    start_date = models.DateField(
        help_text=_('Contract start date')
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Contract end date (optional for open-ended contracts)')
    )
    status = models.CharField(
        max_length=20,
        choices=ContractStatus.choices,
        default=ContractStatus.DRAFT,
        help_text=_('Current contract status')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp when both parties signed')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp when contract was completed')
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['client', 'status', '-created_at']),
            models.Index(fields=['provider', 'status', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.client.email} & {self.provider.email}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError('End date cannot be before start date.')

    def is_fully_signed(self):
        """Check if both client and provider have signed"""
        return (
            self.signatures.filter(signer=self.client, is_signed=True).exists() and
            self.signatures.filter(signer=self.provider, is_signed=True).exists()
        )


class ContractMilestone(models.Model):
    class MilestoneStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='milestones',
        help_text=_('The contract this milestone belongs to')
    )
    title = models.CharField(
        max_length=200,
        help_text=_('Milestone title')
    )
    description = models.TextField(
        blank=True,
        help_text=_('Milestone description')
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Payment amount for this milestone')
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text=_('Expected completion date')
    )
    status = models.CharField(
        max_length=20,
        choices=MilestoneStatus.choices,
        default=MilestoneStatus.PENDING,
        help_text=_('Current milestone status')
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text=_('Order of milestone in the contract')
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp when milestone was completed')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['contract', 'order']),
        ]

    def __str__(self):
        return f"{self.contract.title} - {self.title}"


class TimeEntry(models.Model):
    """Provider logs hours worked; client approves and pays (hourly contracts)."""
    class TimeEntryStatus(models.TextChoices):
        PENDING_APPROVAL = 'PENDING_APPROVAL', _('Pending Approval')
        APPROVED = 'APPROVED', _('Approved')
        REJECTED = 'REJECTED', _('Rejected')
        PAID = 'PAID', _('Paid')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='time_entries',
        help_text=_('The contract this time entry belongs to')
    )
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='time_entries',
        help_text=_('The provider who logged the hours')
    )
    date = models.DateField(help_text=_('Date of work'))
    hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Hours worked')
    )
    description = models.TextField(
        blank=True,
        help_text=_('Optional description of work done')
    )
    status = models.CharField(
        max_length=20,
        choices=TimeEntryStatus.choices,
        default=TimeEntryStatus.PENDING_APPROVAL,
        help_text=_('PENDING_APPROVAL → client approves → APPROVED → client pays → PAID')
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='approved_time_entries',
        null=True,
        blank=True,
        help_text=_('Client who approved (if approved)')
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['contract', 'status']),
            models.Index(fields=['contract', 'date']),
            models.Index(fields=['provider', '-date']),
        ]
        verbose_name_plural = 'Time entries'

    def __str__(self):
        return f"{self.contract.title} - {self.date} ({self.hours}h)"

    @property
    def amount(self):
        """Calculated amount: hours * contract.hourly_rate."""
        if self.contract.hourly_rate is not None:
            return self.hours * self.contract.hourly_rate
        return None


class ContractSignature(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='signatures',
        help_text=_('The contract being signed')
    )
    signer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contract_signatures',
        help_text=_('The user signing the contract')
    )
    is_signed = models.BooleanField(
        default=False,
        help_text=_('Whether the contract has been signed')
    )
    signature_data = models.TextField(
        blank=True,
        help_text=_('Signature data (can be image data, hash, or text signature)')
    )
    signature_type = models.CharField(
        max_length=20,
        default='DIGITAL',
        choices=[
            ('DIGITAL', _('Digital Signature')),
            ('IMAGE', _('Image Signature')),
            ('TEXT', _('Text Signature')),
        ],
        help_text=_('Type of signature')
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text=_('IP address from which signature was made')
    )
    user_agent = models.TextField(
        blank=True,
        help_text=_('User agent from which signature was made')
    )
    signed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp when signature was made')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['contract', 'signer']
        indexes = [
            models.Index(fields=['contract', 'is_signed']),
            models.Index(fields=['signer', '-signed_at']),
        ]

    def __str__(self):
        status = "Signed" if self.is_signed else "Pending"
        return f"{self.contract.title} - {self.signer.email} ({status})"
