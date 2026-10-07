import logging

from celery import shared_task
from django.contrib.auth import get_user_model

from .models import Notification
from .realtime import broadcast_notification_created

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    ignore_result=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    max_retries=5,
    soft_time_limit=20,
    time_limit=30,
)
def send_in_app_notification(
    self,
    recipient_id,
    title,
    message='',
    link='',
    actor_id=None,
):
    """
    Create an in-app notification for a user, then push to their inbox socket.

    Prefer enqueue_in_app_notification(...) from views so broker failures
    fall back to a synchronous create instead of dropping the alert.
    """
    recipient = User.objects.filter(pk=recipient_id).first()
    if not recipient:
        logger.warning('Notification skipped: recipient %s not found', recipient_id)
        return None
    actor = User.objects.filter(pk=actor_id).first() if actor_id else None
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message or '',
        link=link or '',
        actor=actor,
    )
    try:
        broadcast_notification_created(notification)
    except Exception:
        logger.exception(
            'Failed to broadcast notification %s to inbox_%s',
            notification.id,
            recipient_id,
        )
    return str(notification.id)


def enqueue_in_app_notification(
    recipient_id,
    title,
    message='',
    link='',
    actor_id=None,
):
    """
    Queue a notification via Celery. If the broker is unreachable, create it
    synchronously so the user still gets the alert (and live push still runs).
    """
    kwargs = {
        'recipient_id': recipient_id,
        'title': title,
        'message': message,
        'link': link,
        'actor_id': actor_id,
    }
    try:
        send_in_app_notification.delay(**kwargs)
    except Exception:
        logger.exception(
            'Celery enqueue failed for notification "%s"; creating synchronously',
            title,
        )
        send_in_app_notification.apply(kwargs=kwargs)
