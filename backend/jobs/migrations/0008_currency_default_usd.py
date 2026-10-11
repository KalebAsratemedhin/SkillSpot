from django.db import migrations, models


def etb_to_usd(apps, schema_editor):
    Job = apps.get_model('jobs', 'Job')
    Job.objects.filter(currency__iexact='ETB').update(currency='USD')


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0007_job_address_and_location_coords'),
    ]

    operations = [
        migrations.AlterField(
            model_name='job',
            name='currency',
            field=models.CharField(default='USD', max_length=3),
        ),
        migrations.RunPython(etb_to_usd, migrations.RunPython.noop),
    ]
