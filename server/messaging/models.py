import uuid
from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from jobs.models import Job

User = get_user_model()


class Conversation(models.Model):
    """
    Represents a conversation thread between two users (client and provider).
    Can be optionally linked to a job for job-related conversations.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.SET_NULL,
        related_name='conversations',
        null=True,
        blank=True,
        help_text=_('Optional: Link to a job for job-related conversations')
    )
    participant1 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant1',
        help_text=_('First participant in the conversation')
    )
    participant2 = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations_as_participant2',
        help_text=_('Second participant in the conversation')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp of the last message in this conversation')
    )

    class Meta:
        ordering = ['-last_message_at', '-updated_at']
        indexes = [
            models.Index(fields=['participant1', '-last_message_at']),
            models.Index(fields=['participant2', '-last_message_at']),
            models.Index(fields=['job', '-last_message_at']),
        ]
        # Note: unique_together with NULL values requires careful handling
        # The serializer/view will ensure proper uniqueness logic
        unique_together = [['participant1', 'participant2', 'job']]

    def __str__(self):
        job_info = f" - {self.job.title}" if self.job else ""
        return f"{self.participant1.email} & {self.participant2.email}{job_info}"

    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        if user == self.participant1:
            return self.participant2
        return self.participant1

    def get_unread_count(self, user):
        return self.messages.exclude(sender=user).filter(is_read=False).count()


class Message(models.Model):
    """
    Individual message within a conversation.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text=_('The conversation this message belongs to')
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        help_text=_('User who sent the message')
    )
    content = models.TextField(
        help_text=_('Message content')
    )
    is_read = models.BooleanField(
        default=False,
        help_text=_('Whether the message has been read by the recipient')
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_('Timestamp when the message was read')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['sender', '-created_at']),
            models.Index(fields=['conversation', 'is_read']),
        ]

    def __str__(self):
        return f"{self.sender.email}: {self.content[:50]}..."

    def mark_as_read(self):
        """Mark the message as read"""
        if not self.is_read:
            from django.utils import timezone
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class MessageAttachment(models.Model):
    """
    Optional file attachments for messages.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text=_('The message this attachment belongs to')
    )
    file = models.FileField(
        upload_to='message_attachments/%Y/%m/%d/',
        help_text=_('Uploaded file')
    )
    file_name = models.CharField(
        max_length=255,
        help_text=_('Original file name')
    )
    file_size = models.PositiveIntegerField(
        help_text=_('File size in bytes')
    )
    file_type = models.CharField(
        max_length=100,
        blank=True,
        help_text=_('File MIME type')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.message.id} - {self.file_name}"
