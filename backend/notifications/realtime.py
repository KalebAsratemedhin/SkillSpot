"""
Push in-app notifications to the user's inbox WebSocket group.
"""
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification


def unread_notification_count(recipient_id) -> int:
    return Notification.objects.filter(recipient_id=recipient_id, read=False).count()


def serialize_notification(notification: Notification) -> dict:
    actor = notification.actor
    return {
        'id': str(notification.id),
        'recipient': str(notification.recipient_id),
        'title': notification.title,
        'message': notification.message or '',
        'link': notification.link or '',
        'actor': str(actor.id) if actor else None,
        'actor_email': actor.email if actor else None,
        'read': notification.read,
        'read_at': notification.read_at.isoformat() if notification.read_at else None,
        'created_at': (
            notification.created_at.isoformat() if notification.created_at else None
        ),
    }


def broadcast_to_user_inbox(recipient_id, payload: dict) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        f'inbox_{recipient_id}',
        {
            'type': 'inbox_event',
            'payload': payload,
        },
    )


def broadcast_notification_created(notification: Notification) -> None:
    recipient_id = notification.recipient_id
    broadcast_to_user_inbox(
        recipient_id,
        {
            'type': 'notification_created',
            'notification': serialize_notification(notification),
            'unread_count': unread_notification_count(recipient_id),
        },
    )


def broadcast_notification_updated(notification: Notification) -> None:
    recipient_id = notification.recipient_id
    broadcast_to_user_inbox(
        recipient_id,
        {
            'type': 'notification_updated',
            'notification': serialize_notification(notification),
            'unread_count': unread_notification_count(recipient_id),
        },
    )


def broadcast_notifications_read(recipient_id, *, marked: int) -> None:
    broadcast_to_user_inbox(
        recipient_id,
        {
            'type': 'notifications_read',
            'marked': marked,
            'unread_count': unread_notification_count(recipient_id),
        },
    )
