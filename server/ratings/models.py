import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.db.models import Avg, Count
from jobs.models import Job
from contracts.models import Contract

User = get_user_model()


class Rating(models.Model):
    """
    Bidirectional rating system - can rate both client and provider
    """
    class RatingType(models.TextChoices):
        CLIENT_TO_PROVIDER = 'CLIENT_TO_PROVIDER', _('Client to Provider')
        PROVIDER_TO_CLIENT = 'PROVIDER_TO_CLIENT', _('Provider to Client')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='ratings',
        null=True,
        blank=True,
        help_text=_('The job this rating is for')
    )
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='ratings',
        null=True,
        blank=True,
        help_text=_('The contract this rating is for')
    )
    rater = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ratings_given',
        help_text=_('User giving the rating')
    )
    rated_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ratings_received',
        help_text=_('User being rated')
    )
    rating_type = models.CharField(
        max_length=20,
        choices=RatingType.choices,
        help_text=_('Type of rating (client to provider or vice versa)')
    )
    score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating score from 1 to 5')
    )
    comment = models.TextField(
        blank=True,
        help_text=_('Optional comment/review')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['rated_user', '-created_at']),
            models.Index(fields=['rater', '-created_at']),
            models.Index(fields=['job', 'rating_type']),
            models.Index(fields=['contract', 'rating_type']),
        ]
        # Ensure one rating per rater per job/contract per type
        unique_together = [
            ['job', 'rater', 'rating_type'],
            ['contract', 'rater', 'rating_type'],
        ]

    def __str__(self):
        return f"{self.rater.email} -> {self.rated_user.email}: {self.score}/5"

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure either job or contract is provided, but not both
        if not self.job and not self.contract:
            raise ValidationError('Either job or contract must be provided.')
        if self.job and self.contract:
            raise ValidationError('Cannot provide both job and contract.')
        
        # Validate job/contract status
        if self.job:
            if self.job.status != Job.JobStatus.COMPLETED:
                raise ValidationError('Can only rate completed jobs.')
        if self.contract:
            if self.contract.status != Contract.ContractStatus.COMPLETED:
                raise ValidationError('Can only rate completed contracts.')
        
        # Validate rater and rated_user based on rating type
        if self.job:
            if self.rating_type == self.RatingType.CLIENT_TO_PROVIDER:
                if self.rater != self.job.client:
                    raise ValidationError('Only the client can rate the provider.')
                # Provider should be from accepted application or invitation
                # This will be validated in the serializer
            elif self.rating_type == self.RatingType.PROVIDER_TO_CLIENT:
                if self.rater.user_type not in ['PROVIDER', 'BOTH']:
                    raise ValidationError('Only providers can rate clients.')
        
        if self.contract:
            if self.rating_type == self.RatingType.CLIENT_TO_PROVIDER:
                if self.rater != self.contract.client or self.rated_user != self.contract.provider:
                    raise ValidationError('Invalid rater/rated_user for contract rating.')
            elif self.rating_type == self.RatingType.PROVIDER_TO_CLIENT:
                if self.rater != self.contract.provider or self.rated_user != self.contract.client:
                    raise ValidationError('Invalid rater/rated_user for contract rating.')

    @classmethod
    def calculate_average_rating(cls, user, rating_type=None):
        """
        Calculate average rating for a user
        If rating_type is provided, only calculate for that type
        """
        queryset = cls.objects.filter(rated_user=user)
        
        if rating_type:
            queryset = queryset.filter(rating_type=rating_type)
        
        result = queryset.aggregate(
            average=Avg('score'),
            count=Count('id')
        )
        
        return {
            'average': round(result['average'] or 0, 2),
            'count': result['count'] or 0
        }

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        # Update provider profile average rating if rating is for a provider
        if self.rating_type == self.RatingType.CLIENT_TO_PROVIDER:
            if hasattr(self.rated_user, 'profile') and hasattr(self.rated_user.profile, 'provider_profile'):
                provider_profile = self.rated_user.profile.provider_profile
                rating_stats = Rating.calculate_average_rating(
                    self.rated_user,
                    rating_type=self.RatingType.CLIENT_TO_PROVIDER
                )
                provider_profile.average_rating = rating_stats['average']
                provider_profile.save(update_fields=['average_rating'])
