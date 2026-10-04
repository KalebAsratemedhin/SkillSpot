from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Conversation, Message, MessageAttachment
from jobs.models import Job

User = get_user_model()


class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = (
            'id', 'file', 'file_name', 'file_size', 'file_type', 'created_at'
        )
        read_only_fields = ('id', 'file_size', 'file_type', 'created_at')


class MessageSerializer(serializers.ModelSerializer):
    sender_email = serializers.EmailField(source='sender.email', read_only=True)
    sender_name = serializers.SerializerMethodField()
    attachments = MessageAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = Message
        fields = (
            'id', 'conversation', 'sender', 'sender_email', 'sender_name',
            'content', 'is_read', 'read_at', 'attachments',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'sender', 'sender_email', 'sender_name',
            'is_read', 'read_at', 'created_at', 'updated_at'
        )

    def get_sender_name(self, obj):
        if hasattr(obj.sender, 'profile') and obj.sender.profile:
            return obj.sender.profile.full_name
        return obj.sender.email


class MessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ('content',)

    def validate(self, attrs):
        conversation = self.context['conversation']
        sender = self.context['sender']

        # Verify sender is a participant in the conversation
        if sender not in [conversation.participant1, conversation.participant2]:
            raise serializers.ValidationError(
                'You are not a participant in this conversation.'
            )

        return attrs

    def create(self, validated_data):
        conversation = self.context['conversation']
        sender = self.context['sender']

        message = Message.objects.create(
            conversation=conversation,
            sender=sender,
            **validated_data
        )

        # Update conversation's last_message_at
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=['last_message_at'])

        return message


class ConversationSerializer(serializers.ModelSerializer):
    participant1_email = serializers.EmailField(source='participant1.email', read_only=True)
    participant1_name = serializers.SerializerMethodField()
    participant2_email = serializers.EmailField(source='participant2.email', read_only=True)
    participant2_name = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='job.title', read_only=True, allow_null=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    other_participant = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            'id', 'job', 'job_title', 'participant1', 'participant1_email',
            'participant1_name', 'participant2', 'participant2_email',
            'participant2_name', 'other_participant', 'last_message',
            'unread_count', 'created_at', 'updated_at', 'last_message_at'
        )
        read_only_fields = (
            'id', 'participant1', 'participant2', 'created_at', 'updated_at',
            'last_message_at'
        )

    def get_participant1_name(self, obj):
        if hasattr(obj.participant1, 'profile') and obj.participant1.profile:
            return obj.participant1.profile.full_name
        return obj.participant1.email

    def get_participant2_name(self, obj):
        if hasattr(obj.participant2, 'profile') and obj.participant2.profile:
            return obj.participant2.profile.full_name
        return obj.participant2.email

    def get_last_message(self, obj):
        last_message = obj.messages.last()
        if last_message:
            return {
                'id': str(last_message.id),
                'content': last_message.content[:100],  # Truncate for preview
                'sender_email': last_message.sender.email,
                'created_at': last_message.created_at
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.get_unread_count(request.user)
        return 0

    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user:
            other = obj.get_other_participant(request.user)
            return {
                'id': str(other.id),
                'email': other.email,
                'name': other.profile.full_name if hasattr(other, 'profile') and other.profile else other.email
            }
        return None


class ConversationCreateSerializer(serializers.Serializer):
    participant2_id = serializers.UUIDField(required=True)
    job_id = serializers.UUIDField(required=False, allow_null=True)
    initial_message = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        participant1 = self.context['participant1']
        participant2_id = attrs.get('participant2_id')
        job_id = attrs.get('job_id')

        # Validate participant2
        try:
            participant2 = User.objects.get(id=participant2_id)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'participant2_id': 'User not found.'
            })

        if participant1 == participant2:
            raise serializers.ValidationError({
                'participant2_id': 'You cannot start a conversation with yourself.'
            })

        # Validate job if provided
        if job_id:
            try:
                job = Job.objects.get(id=job_id)
                # Verify participant1 is the client
                if job.client != participant1:
                    raise serializers.ValidationError({
                        'job_id': 'You can only create job-related conversations for your own jobs.'
                    })
                # Verify participant2 is a provider (could be from an application)
                if participant2.user_type not in ['PROVIDER', 'BOTH']:
                    raise serializers.ValidationError({
                        'participant2_id': 'The other participant must be a service provider for job-related conversations.'
                    })
            except Job.DoesNotExist:
                raise serializers.ValidationError({
                    'job_id': 'Job not found.'
                })

        return attrs

    def create(self, validated_data):
        initiator = self.context['participant1']  # The user creating the conversation
        participant2_id = validated_data['participant2_id']
        job_id = validated_data.get('job_id')
        initial_message = validated_data.get('initial_message', '')

        participant2 = User.objects.get(id=participant2_id)
        job = Job.objects.get(id=job_id) if job_id else None

        # Ensure consistent ordering (smaller UUID first for participant1)
        # This ensures we can find existing conversations regardless of who initiated
        if initiator.id > participant2.id:
            participant1, participant2 = participant2, initiator
        else:
            participant1, participant2 = initiator, participant2

        conversation, created = Conversation.objects.get_or_create(
            participant1=participant1,
            participant2=participant2,
            job=job,
            defaults={}
        )

        # Send initial message if provided
        if initial_message and created:
            Message.objects.create(
                conversation=conversation,
                sender=initiator,  # Use original initiator, not swapped participant1
                content=initial_message
            )
            conversation.last_message_at = timezone.now()
            conversation.save(update_fields=['last_message_at'])

        return conversation


class MessageMarkReadSerializer(serializers.Serializer):
    message_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
        help_text='Optional list of message IDs to mark as read; if empty, all unread in conversation are marked'
    )

    def validate(self, attrs):
        message_ids = attrs.get('message_ids') or []
        user = self.context['user']
        conversation = self.context.get('conversation')

        if message_ids:
            messages = Message.objects.filter(id__in=message_ids)
            if conversation:
                messages = messages.filter(conversation=conversation)
            invalid_messages = messages.filter(sender=user)
            if invalid_messages.exists():
                raise serializers.ValidationError({
                    'message_ids': 'You cannot mark your own messages as read.'
                })
            for message in messages:
                if user not in [message.conversation.participant1, message.conversation.participant2]:
                    raise serializers.ValidationError({
                        'message_ids': 'You are not authorized to mark these messages as read.'
                    })
        return attrs

    def save(self):
        message_ids = self.validated_data.get('message_ids') or []
        user = self.context['user']
        conversation = self.context.get('conversation')

        if message_ids:
            messages = Message.objects.filter(id__in=message_ids)
        elif conversation:
            # Mark all unread messages in this conversation (where user is recipient)
            messages = Message.objects.filter(
                conversation=conversation
            ).exclude(sender=user).filter(is_read=False)
        else:
            messages = Message.objects.none()

        now = timezone.now()
        updated = messages.update(is_read=True, read_at=now)
        return updated
