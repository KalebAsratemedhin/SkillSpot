import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Notification(models.Model):
    """In-app notification for a user. Created synchronously or via Celery."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    recipient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text=_('User who receives this notification'),
    )
    title = models.CharField(
        max_length=255,
        help_text=_('Short title'),
    )
    message = models.TextField(
        blank=True,
        help_text=_('Optional longer message'),
    )
    link = models.CharField(
        max_length=500,
        blank=True,
        help_text=_('Optional URL or path to open when clicked'),
    )
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications_triggered',
        help_text=_('User who triggered this notification (e.g. applicant, client)'),
    )
    read = models.BooleanField(
        default=False,
        help_text=_('Whether the recipient has read it'),
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('When the notification was read'),
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'read']),
        ]

    def __str__(self):
        return f"{self.title} -> {self.recipient_id}"







