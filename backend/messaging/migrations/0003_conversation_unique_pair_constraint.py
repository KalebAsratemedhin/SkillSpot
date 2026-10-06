# Enforce one conversation per ordered user pair (separate from data merge txn).

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0002_conversation_unique_pair'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='conversation',
            name='job',
            field=models.ForeignKey(
                blank=True,
                help_text='Optional context only; rooms are per user pair, not per job',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='conversations',
                to='jobs.job',
            ),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='participant1',
            field=models.ForeignKey(
                help_text='First participant (lower UUID)',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='conversations_as_participant1',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='conversation',
            name='participant2',
            field=models.ForeignKey(
                help_text='Second participant (higher UUID)',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='conversations_as_participant2',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddConstraint(
            model_name='conversation',
            constraint=models.UniqueConstraint(
                fields=('participant1', 'participant2'),
                name='messaging_conversation_unique_pair',
            ),
        ),
    ]
