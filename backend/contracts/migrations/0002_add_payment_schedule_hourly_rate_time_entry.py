# Generated manually for payment_schedule, hourly_rate, TimeEntry

import django.core.validators
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contract',
            name='payment_schedule',
            field=models.CharField(
                choices=[('FIXED', 'Fixed Price'), ('HOURLY', 'Hourly')],
                default='FIXED',
                help_text='FIXED = pay once; HOURLY = provider logs hours, client approves and pays',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='contract',
            name='hourly_rate',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Rate per hour (for HOURLY contracts only)',
                max_digits=10,
                null=True,
                validators=[django.core.validators.MinValueValidator(0)],
            ),
        ),
        migrations.CreateModel(
            name='TimeEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('date', models.DateField(help_text='Date of work')),
                ('hours', models.DecimalField(decimal_places=2, help_text='Hours worked', max_digits=6, validators=[django.core.validators.MinValueValidator(0)])),
                ('description', models.TextField(blank=True, help_text='Optional description of work done')),
                ('status', models.CharField(choices=[('PENDING_APPROVAL', 'Pending Approval'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'), ('PAID', 'Paid')], default='PENDING_APPROVAL', help_text='PENDING_APPROVAL → client approves → APPROVED → client pays → PAID', max_length=20)),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('approved_by', models.ForeignKey(blank=True, help_text='Client who approved (if approved)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='approved_time_entries', to=settings.AUTH_USER_MODEL)),
                ('contract', models.ForeignKey(help_text='The contract this time entry belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='time_entries', to='contracts.contract')),
                ('provider', models.ForeignKey(help_text='The provider who logged the hours', on_delete=django.db.models.deletion.CASCADE, related_name='time_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-date', '-created_at'],
                'verbose_name_plural': 'Time entries',
            },
        ),
        migrations.AddIndex(
            model_name='timeentry',
            index=models.Index(fields=['contract', 'status'], name='contracts_t_contrac_te_idx'),
        ),
        migrations.AddIndex(
            model_name='timeentry',
            index=models.Index(fields=['contract', 'date'], name='contracts_t_contrac_date_idx'),
        ),
        migrations.AddIndex(
            model_name='timeentry',
            index=models.Index(fields=['provider', '-date'], name='contracts_t_provide_date_idx'),
        ),
    ]
