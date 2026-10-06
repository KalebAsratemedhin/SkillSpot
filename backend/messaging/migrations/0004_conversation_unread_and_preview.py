# Denormalized unread counters + last-message preview; backfill from Message rows.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models
def backfill_unread_and_preview(apps, schema_editor):
    Conversation = apps.get_model('messaging', 'Conversation')
    Message = apps.get_model('messaging', 'Message')

    for conv in Conversation.objects.all().iterator():
        p1_unread = (
            Message.objects.filter(conversation_id=conv.id, is_read=False)
            .exclude(sender_id=conv.participant1_id)
            .count()
        )
        p2_unread = (
            Message.objects.filter(conversation_id=conv.id, is_read=False)
            .exclude(sender_id=conv.participant2_id)
            .count()
        )
        last = (
            Message.objects.filter(conversation_id=conv.id)
            .order_by('-created_at')
            .first()
        )
        conv.participant1_unread = p1_unread
        conv.participant2_unread = p2_unread
        if last:
            conv.last_message_preview = (last.content or '')[:100]
            conv.last_message_sender_id = last.sender_id
            if not conv.last_message_at:
                conv.last_message_at = last.created_at
        conv.save(
            update_fields=[
                'participant1_unread',
                'participant2_unread',
                'last_message_preview',
                'last_message_sender_id',
                'last_message_at',
            ]
        )


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0003_conversation_unique_pair_constraint'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='conversation',
            name='last_message_preview',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Truncated preview of the latest message',
                max_length=100,
            ),
        ),
        migrations.AddField(
            model_name='conversation',
            name='last_message_sender',
            field=models.ForeignKey(
                blank=True,
                help_text='Sender of the latest message',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='+',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name='conversation',
            name='participant1_unread',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Unread messages for participant1',
            ),
        ),
        migrations.AddField(
            model_name='conversation',
            name='participant2_unread',
            field=models.PositiveIntegerField(
                default=0,
                help_text='Unread messages for participant2',
            ),
        ),
        migrations.RunPython(backfill_unread_and_preview, noop_reverse),
    ]
