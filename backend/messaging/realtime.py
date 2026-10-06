"""
Real-time chat + inbox fan-out via Django Channels.
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db.models import Sum


def serialize_message_for_ws(msg):
    attachments = []
    try:
        for att in msg.attachments.all():
            attachments.append({
                'id': str(att.id),
                'file': att.file.url if att.file else None,
                'file_name': att.file_name,
                'file_size': att.file_size,
                'file_type': att.file_type,
            })
    except Exception:
        attachments = []
    return {
        'id': str(msg.id),
        'conversation': str(msg.conversation_id),
        'sender': str(msg.sender_id),
        'content': msg.content,
        'is_read': msg.is_read,
        'created_at': msg.created_at.isoformat() if msg.created_at else None,
        'updated_at': msg.updated_at.isoformat() if msg.updated_at else None,
        'sender_email': msg.sender.email if msg.sender else None,
        'attachments': attachments,
    }


def total_unread_for_user(user) -> int:
    """Sum denormalized per-conversation unread counters for a user."""
    from .models import Conversation

    as_p1 = (
        Conversation.objects.filter(participant1=user)
        .aggregate(total=Sum('participant1_unread'))
        .get('total')
        or 0
    )
    as_p2 = (
        Conversation.objects.filter(participant2=user)
        .aggregate(total=Sum('participant2_unread'))
        .get('total')
        or 0
    )
    return int(as_p1) + int(as_p2)


def inbox_conversation_payload(conversation, for_user):
    """Slice of a conversation the inbox UI needs to patch its list."""
    sender = conversation.last_message_sender
    last_message = None
    if conversation.last_message_preview or conversation.last_message_at:
        last_message = {
            'id': None,
            'content': conversation.last_message_preview or '',
            'sender_email': sender.email if sender else None,
            'created_at': (
                conversation.last_message_at.isoformat()
                if conversation.last_message_at
                else None
            ),
        }
    return {
        'id': str(conversation.id),
        'last_message': last_message,
        'last_message_at': (
            conversation.last_message_at.isoformat()
            if conversation.last_message_at
            else None
        ),
        'unread_count': conversation.unread_for(for_user),
        'updated_at': conversation.updated_at.isoformat() if conversation.updated_at else None,
    }


def broadcast_chat_message(conversation_id, message_payload):
    """Push a message to all WebSocket clients in the conversation group."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f'chat_{conversation_id}',
        {
            'type': 'chat_message',
            'message': message_payload,
        },
    )


def broadcast_inbox_update(user_id, conversation, *, event='conversation_updated'):
    """
    Push an inbox patch to one user's inbox socket(s).

    Frame shape (JSON on the wire via InboxConsumer.inbox_event):
    {
      "type": "inbox_update",
      "event": "conversation_updated" | "conversation_read",
      "conversation": { id, last_message, last_message_at, unread_count, updated_at },
      "total_unread": <int>
    }
    """
    from .models import Conversation
    from django.contrib.auth import get_user_model

    User = get_user_model()
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    # Refresh counters / preview if we were passed a stale instance.
    if isinstance(conversation, Conversation):
        conversation.refresh_from_db()

    payload = {
        'type': 'inbox_update',
        'event': event,
        'conversation': inbox_conversation_payload(conversation, user),
        'total_unread': total_unread_for_user(user),
    }
    async_to_sync(channel_layer.group_send)(
        f'inbox_{user_id}',
        {
            'type': 'inbox_event',
            'payload': payload,
        },
    )


def broadcast_inbox_to_participants(conversation, *, event='conversation_updated', exclude_user_id=None):
    for uid in (conversation.participant1_id, conversation.participant2_id):
        if exclude_user_id is not None and str(uid) == str(exclude_user_id):
            continue
        broadcast_inbox_update(uid, conversation, event=event)
