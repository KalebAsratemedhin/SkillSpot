"""
Message write path: persist, update denormalized counters/previews, fan out.
"""
from django.db.models import F
from django.utils import timezone

from .models import Conversation, Message
from .realtime import (
    broadcast_chat_message,
    broadcast_inbox_to_participants,
    serialize_message_for_ws,
)


MAX_MESSAGE_LENGTH = 5000


def create_and_broadcast_message(
    *,
    conversation: Conversation,
    sender,
    content: str,
    allow_empty: bool = False,
) -> Message:
    """
    Create a message, bump the recipient's unread counter, update preview,
    broadcast to the open chat room and both users' inbox sockets.
    """
    text = (content or '').strip()
    if not text:
        if not allow_empty:
            raise ValueError('Message content is empty.')
        text = ''
    if len(text) > MAX_MESSAGE_LENGTH:
        raise ValueError(f'Message exceeds {MAX_MESSAGE_LENGTH} characters.')

    if sender.id not in (conversation.participant1_id, conversation.participant2_id):
        raise PermissionError('Sender is not a participant.')

    msg = Message.objects.create(
        conversation=conversation,
        sender=sender,
        content=text,
    )

    now = timezone.now()
    preview = text[:100] if text else 'Shared a file'
    recipient_is_p1 = sender.id == conversation.participant2_id

    updates = {
        'last_message_at': now,
        'last_message_preview': preview,
        'last_message_sender_id': sender.id,
        'updated_at': now,
    }
    if recipient_is_p1:
        updates['participant1_unread'] = F('participant1_unread') + 1
    else:
        updates['participant2_unread'] = F('participant2_unread') + 1

    Conversation.objects.filter(pk=conversation.pk).update(**updates)
    conversation.refresh_from_db()

    payload = serialize_message_for_ws(msg)
    broadcast_chat_message(conversation.id, payload)
    broadcast_inbox_to_participants(conversation, event='conversation_updated')
    return msg


def mark_conversation_read(*, conversation: Conversation, user) -> int:
    """
    Mark the other party's messages as read, zero this user's unread counter,
    notify their inbox socket.
    """
    if user.id not in (conversation.participant1_id, conversation.participant2_id):
        raise PermissionError('User is not a participant.')

    now = timezone.now()
    updated = (
        Message.objects.filter(conversation=conversation, is_read=False)
        .exclude(sender=user)
        .update(is_read=True, read_at=now)
    )

    if user.id == conversation.participant1_id:
        Conversation.objects.filter(pk=conversation.pk).update(participant1_unread=0)
    else:
        Conversation.objects.filter(pk=conversation.pk).update(participant2_unread=0)

    conversation.refresh_from_db()
    from .realtime import broadcast_inbox_update
    broadcast_inbox_update(user.id, conversation, event='conversation_read')
    return updated
