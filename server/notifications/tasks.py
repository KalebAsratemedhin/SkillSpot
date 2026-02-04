from celery import shared_task
from django.contrib.auth import get_user_model
from .models import Notification

User = get_user_model()


@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=True, max_retries=3)
def send_in_app_notification(
    self,
    recipient_id,
    title,
    message='',
    link='',
    actor_id=None,
):
    """
    Create an in-app notification for a user. Call from views or other tasks with:
        send_in_app_notification.delay(recipient_id, 'Title', 'Message', link='/jobs/123/', actor_id=applicant_id)
    """
    recipient = User.objects.filter(pk=recipient_id).first()
    if not recipient:
        return None
    actor = User.objects.filter(pk=actor_id).first() if actor_id else None
    notification = Notification.objects.create(
        recipient=recipient,
        title=title,
        message=message or '',
        link=link or '',
        actor=actor,
    )
    return str(notification.id)







