from django.core.exceptions import ValidationError
import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Profile(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        null=True
    )
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    timezone = models.CharField(max_length=50, default='UTC')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email}'s Profile"

    @property
    def full_name(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.user.email


class Tag(models.Model):
    class TagCategory(models.TextChoices):
        SKILL = 'SKILL', _('Skill/Service Type')
        CERTIFICATION = 'CERTIFICATION', _('Certification/License')
        LANGUAGE = 'LANGUAGE', _('Language')
        OTHER = 'OTHER', _('Other')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(
        max_length=20,
        choices=TagCategory.choices,
        default=TagCategory.SKILL
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class ServiceProviderProfile(models.Model):
    class AvailabilityStatus(models.TextChoices):
        AVAILABLE = 'AVAILABLE', _('Available')
        BUSY = 'BUSY', _('Busy')
        UNAVAILABLE = 'UNAVAILABLE', _('Unavailable')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    profile = models.OneToOneField(
        Profile,
        on_delete=models.CASCADE,
        related_name='provider_profile'
    )
    hourly_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )
    availability_status = models.CharField(
        max_length=20,
        choices=AvailabilityStatus.choices,
        default=AvailabilityStatus.AVAILABLE
    )
    years_of_experience = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MaxValueValidator(100)]
    )
    service_radius = models.PositiveIntegerField(null=True, blank=True)
    languages = models.ManyToManyField(
        Tag,
        related_name='speakers',
        blank=True,
        limit_choices_to={'category': Tag.TagCategory.LANGUAGE}
    )
    skills = models.ManyToManyField(
        Tag,
        related_name='providers',
        blank=True,
        limit_choices_to={'category': Tag.TagCategory.SKILL}
    )
    certifications = models.ManyToManyField(
        Tag,
        related_name='certified_providers',
        blank=True,
        limit_choices_to={'category': Tag.TagCategory.CERTIFICATION}
    )
    portfolio_visibility = models.BooleanField(default=True)
    total_jobs_completed = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_earnings = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    # Stripe Connect fields
    stripe_account_id = models.CharField(
        max_length=255,
        blank=True,
        help_text=_('Stripe Connect account ID (acct_xxx)')
    )
    stripe_account_enabled = models.BooleanField(
        default=False,
        help_text=_('Whether the Stripe account is enabled to receive payments')
    )
    stripe_onboarding_completed = models.BooleanField(
        default=False,
        help_text=_('Whether Stripe onboarding is completed')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-average_rating', '-total_jobs_completed']

    def __str__(self):
        return f"{self.profile.user.email}'s Provider Profile"

    @property
    def user(self):
        return self.profile.user


class Experience(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    provider = models.ForeignKey(
        ServiceProviderProfile,
        on_delete=models.CASCADE,
        related_name='experiences'
    )
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', '-is_current']
        indexes = [
            models.Index(fields=['provider', '-start_date']),
        ]

    def __str__(self):
        return f"{self.title} at {self.company_name or 'Various'}"

    def clean(self):
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValidationError('End date must be after start date.')
        if self.is_current and self.end_date:
            raise ValidationError('Current position cannot have an end date.')
