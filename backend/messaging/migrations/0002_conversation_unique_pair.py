# Drop per-job uniqueness and merge duplicate pair rooms into one conversation.

from django.db import migrations


def merge_pair_conversations(apps, schema_editor):
    Conversation = apps.get_model('messaging', 'Conversation')
    Message = apps.get_model('messaging', 'Message')

    seen = {}
    for conv in Conversation.objects.all().order_by('-last_message_at', '-updated_at', '-created_at'):
        key = (str(conv.participant1_id), str(conv.participant2_id))
        if key not in seen:
            seen[key] = conv
            if conv.job_id is not None:
                conv.job_id = None
                conv.save(update_fields=['job_id'])
            continue
        keeper = seen[key]
        Message.objects.filter(conversation_id=conv.id).update(conversation_id=keeper.id)
        conv.delete()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='conversation',
            unique_together=set(),
        ),
        migrations.RemoveIndex(
            model_name='conversation',
            name='messaging_c_job_id_166f34_idx',
        ),
        migrations.RunPython(merge_pair_conversations, noop_reverse),
    ]
