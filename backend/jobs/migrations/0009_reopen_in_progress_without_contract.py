from django.db import migrations


def reopen_jobs_without_contracts(apps, schema_editor):
    """
    Accept used to flip jobs to IN_PROGRESS before a contract existed.
    Reopen those so they stay listed as OPEN until a contract is created.
    """
    Job = apps.get_model('jobs', 'Job')
    Contract = apps.get_model('contracts', 'Contract')
    job_ids_with_contract = Contract.objects.exclude(job_id=None).values_list(
        'job_id', flat=True,
    ).distinct()
    Job.objects.filter(
        status='IN_PROGRESS',
    ).exclude(
        id__in=job_ids_with_contract,
    ).update(status='OPEN')


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0008_currency_default_usd'),
        ('contracts', '0004_currency_default_usd'),
    ]

    operations = [
        migrations.RunPython(reopen_jobs_without_contracts, migrations.RunPython.noop),
    ]
