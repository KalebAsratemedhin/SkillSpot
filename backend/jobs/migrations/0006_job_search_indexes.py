# Generated manually for optional Job search indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0005_alter_job_location_optional'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['payment_schedule'], name='jobs_job_payment_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['budget_min'], name='jobs_job_budget__idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['budget_max'], name='jobs_job_budget_max_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(
                fields=['status', 'payment_schedule', '-created_at'],
                name='jobs_job_status_pay_created_idx',
            ),
        ),
    ]
