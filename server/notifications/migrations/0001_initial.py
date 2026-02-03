# Generated migration for notifications app

import uuid
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(help_text='Short title', max_length=255)),
                ('message', models.TextField(blank=True, help_text='Optional longer message')),
                ('link', models.CharField(blank=True, help_text='Optional URL or path to open when clicked', max_length=500)),
                ('read', models.BooleanField(default=False, help_text='Whether the recipient has read it')),
                ('read_at', models.DateTimeField(blank=True, help_text='When the notification was read', null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(blank=True, help_text='User who triggered this notification (e.g. applicant, client)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications_triggered', to=settings.AUTH_USER_MODEL)),
                ('recipient', models.ForeignKey(help_text='User who receives this notification', on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', '-created_at'], name='notificatio_recipie_created_idx'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'read'], name='notificatio_recipie_read_idx'),
        ),
    ]




