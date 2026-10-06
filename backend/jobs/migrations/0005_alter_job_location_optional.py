# Generated manually for optional Job.location

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0004_job_latitude_longitude'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='location',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Optional text location (city, area, address)',
                max_length=200,
            ),
        ),
    ]
