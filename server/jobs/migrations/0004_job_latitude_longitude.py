# Generated manually for Job map location

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0003_job_payment_schedule_alter_job_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='latitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                help_text='Latitude for map display',
                max_digits=9,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='job',
            name='longitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                help_text='Longitude for map display',
                max_digits=9,
                null=True
            ),
        ),
    ]




