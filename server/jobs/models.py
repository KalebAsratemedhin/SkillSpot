import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from profiles.models import Tag

User = get_user_model()


class Job(models.Model):
    class JobType(models.TextChoices):
        TEMPORARY = 'TEMPORARY', _('Temporary')
        PERMANENT = 'PERMANENT', _('Permanent')
        CONTRACT = 'CONTRACT', _('Contract')

    class JobStatus(models.TextChoices):
        DRAFT = 'DRAFT', _('Draft')
        OPEN = 'OPEN', _('Open')
        IN_PROGRESS = 'IN_PROGRESS', _('In Progress')
        COMPLETED = 'COMPLETED', _('Completed')
        CANCELLED = 'CANCELLED', _('Cancelled')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posted_jobs'
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    job_type = models.CharField(
        max_length=20,
        choices=JobType.choices,
        default=JobType.TEMPORARY
    )
    budget_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    budget_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='ETB')
    location = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    is_remote = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=JobStatus.choices,
        default=JobStatus.DRAFT
    )
    required_skills = models.ManyToManyField(
        Tag,
        related_name='jobs',
        blank=True,
        limit_choices_to={'category': Tag.TagCategory.SKILL}
    )
    deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['location']),
            models.Index(fields=['client', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.client.email}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.budget_min and self.budget_max and self.budget_min > self.budget_max:
            raise ValidationError('Minimum budget cannot be greater than maximum budget.')


class JobApplication(models.Model):
    class ApplicationStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        REJECTED = 'REJECTED', _('Rejected')
        WITHDRAWN = 'WITHDRAWN', _('Withdrawn')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='job_applications'
    )
    cover_letter = models.TextField(blank=True)
    proposed_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    status = models.CharField(
        max_length=20,
        choices=ApplicationStatus.choices,
        default=ApplicationStatus.PENDING
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-applied_at']
        unique_together = ['job', 'provider']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['provider', '-applied_at']),
        ]

    def __str__(self):
        return f"{self.provider.email} - {self.job.title}"


class JobInvitation(models.Model):
    class InvitationStatus(models.TextChoices):
        PENDING = 'PENDING', _('Pending')
        ACCEPTED = 'ACCEPTED', _('Accepted')
        DECLINED = 'DECLINED', _('Declined')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='invitations',
        null=True,
        blank=True
    )
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_invitations'
    )
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=InvitationStatus.choices,
        default=InvitationStatus.PENDING
    )
    invited_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-invited_at']
        indexes = [
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['client', '-invited_at']),
        ]

    def __str__(self):
        return f"{self.client.email} -> {self.provider.email}"
