# Rename job text location → address; coordinates remain lat/lng (API: location object)

from django.db import migrations, models


def copy_location_into_address(apps, schema_editor):
    Job = apps.get_model('jobs', 'Job')
    for job in Job.objects.all().iterator():
        text = (getattr(job, 'location', None) or '').strip()
        if text and not (job.address or '').strip():
            job.address = text
            job.save(update_fields=['address'])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0006_job_search_indexes'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='address',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Optional textual address (city, area, street)',
            ),
        ),
        migrations.RunPython(copy_location_into_address, noop_reverse),
        migrations.RemoveIndex(
            model_name='job',
            name='jobs_job_locatio_8b2f8c_idx',
        ),
        migrations.RemoveField(
            model_name='job',
            name='location',
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(fields=['address'], name='jobs_job_address_idx'),
        ),
        migrations.AddIndex(
            model_name='job',
            index=models.Index(
                fields=['latitude', 'longitude'],
                name='jobs_job_lat_lng_idx',
            ),
        ),
        migrations.AlterField(
            model_name='job',
            name='latitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                help_text='Latitude (part of map location)',
                max_digits=9,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='job',
            name='longitude',
            field=models.DecimalField(
                blank=True,
                decimal_places=6,
                help_text='Longitude (part of map location)',
                max_digits=9,
                null=True,
            ),
        ),
    ]
