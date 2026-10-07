from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Conversation, Message, MessageAttachment
from .services import MAX_MESSAGE_LENGTH, create_and_broadcast_message, mark_conversation_read

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
    content = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = Message
        fields = ('content',)

    def validate_content(self, value):
        text = (value or '').strip()
        if len(text) > MAX_MESSAGE_LENGTH:
            raise serializers.ValidationError(
                f'Message exceeds {MAX_MESSAGE_LENGTH} characters.'
            )
        return text

    def validate(self, attrs):
        conversation = self.context['conversation']
        sender = self.context['sender']
        files = self.context.get('files') or []

        if sender not in [conversation.participant1, conversation.participant2]:
            raise serializers.ValidationError(
                'You are not a participant in this conversation.'
            )

        text = (attrs.get('content') or '').strip()
        if not text and not files:
            raise serializers.ValidationError({
                'content': 'Message content or a file is required.',
            })

        attrs['content'] = text
        return attrs

    def create(self, validated_data):
        from .models import MessageAttachment

        conversation = self.context['conversation']
        sender = self.context['sender']
        files = self.context.get('files') or []
        text = validated_data.get('content') or ''

        message = create_and_broadcast_message(
            conversation=conversation,
            sender=sender,
            content=text,
            allow_empty=bool(files),
        )

        for uploaded in files:
            MessageAttachment.objects.create(
                message=message,
                file=uploaded,
                file_name=getattr(uploaded, 'name', 'file')[:255],
                file_size=int(getattr(uploaded, 'size', 0) or 0),
                file_type=(getattr(uploaded, 'content_type', None) or '')[:100],
            )

        if files:
            from .realtime import broadcast_chat_message, serialize_message_for_ws
            from .models import Conversation as ConversationModel

            preview = text[:100] if text else (files[0].name[:100] if files else 'Shared a file')
            ConversationModel.objects.filter(pk=conversation.pk).update(
                last_message_preview=preview
            )
            # Re-broadcast so peers get attachment metadata.
            message = (
                Message.objects.select_related('sender')
                .prefetch_related('attachments')
                .get(pk=message.pk)
            )
            broadcast_chat_message(conversation.id, serialize_message_for_ws(message))

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
        if not obj.last_message_preview and not obj.last_message_at:
            return None
        sender = obj.last_message_sender
        return {
            'id': None,
            'content': obj.last_message_preview,
            'sender_email': sender.email if sender else None,
            'created_at': obj.last_message_at,
        }

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.unread_for(request.user)
        return 0

    def get_other_participant(self, obj):
        request = self.context.get('request')
        if request and request.user:
            from .presence import snapshot_for_user

            other = obj.get_other_participant(request.user)
            presence = snapshot_for_user(other)
            return {
                'id': str(other.id),
                'email': other.email,
                'name': other.profile.full_name if hasattr(other, 'profile') and other.profile else other.email,
                'is_online': presence['is_online'],
                'last_seen_at': presence['last_seen_at'],
            }
        return None


class ConversationCreateSerializer(serializers.Serializer):
    participant2_id = serializers.UUIDField(required=True)
    # Deprecated: rooms are per user pair only. Accepted then ignored for API compat.
    job_id = serializers.UUIDField(required=False, allow_null=True)
    initial_message = serializers.CharField(required=False, allow_blank=True)

    def validate(self, attrs):
        participant1 = self.context['participant1']
        participant2_id = attrs.get('participant2_id')

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

        attrs.pop('job_id', None)
        attrs['participant2'] = participant2
        return attrs

    def create(self, validated_data):
        initiator = self.context['participant1']
        participant2 = validated_data['participant2']
        initial_message = (validated_data.get('initial_message') or '').strip()

        if initiator.id > participant2.id:
            participant1, participant2 = participant2, initiator
        else:
            participant1, participant2 = initiator, participant2

        conversation = (
            Conversation.objects.filter(
                participant1=participant1,
                participant2=participant2,
            )
            .order_by('-last_message_at', '-updated_at')
            .first()
        )
        if conversation is None:
            conversation = Conversation.objects.create(
                participant1=participant1,
                participant2=participant2,
                job=None,
            )

        if initial_message:
            create_and_broadcast_message(
                conversation=conversation,
                sender=initiator,
                content=initial_message,
            )
            conversation.refresh_from_db()

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

        if not conversation:
            return 0

        # Partial mark-read: update rows then resync denormalized counter from truth.
        if message_ids:
            now = timezone.now()
            updated = (
                Message.objects.filter(id__in=message_ids, conversation=conversation)
                .exclude(sender=user)
                .filter(is_read=False)
                .update(is_read=True, read_at=now)
            )
            remaining = (
                Message.objects.filter(conversation=conversation, is_read=False)
                .exclude(sender=user)
                .count()
            )
            if user.id == conversation.participant1_id:
                Conversation.objects.filter(pk=conversation.pk).update(
                    participant1_unread=remaining
                )
            else:
                Conversation.objects.filter(pk=conversation.pk).update(
                    participant2_unread=remaining
                )
            conversation.refresh_from_db()
            from .realtime import broadcast_inbox_update
            broadcast_inbox_update(user.id, conversation, event='conversation_read')
            return updated

        return mark_conversation_read(conversation=conversation, user=user)
