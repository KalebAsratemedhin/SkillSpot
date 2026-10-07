from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0003_provider_directory_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='last_seen_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Last time the user went offline (presence).',
                null=True,
            ),
        ),
    ]
