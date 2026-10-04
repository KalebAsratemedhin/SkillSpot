# Generated manually for time_entry FK (hourly contracts)

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0002_add_payment_schedule_hourly_rate_time_entry'),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='time_entry',
            field=models.ForeignKey(
                blank=True,
                help_text='Optional: Link to a time entry (hourly contracts)',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='payments',
                to='contracts.timeentry',
            ),
        ),
    ]
