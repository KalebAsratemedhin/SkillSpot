from django.db import migrations, models


def etb_to_usd(apps, schema_editor):
    Contract = apps.get_model('contracts', 'Contract')
    Contract.objects.filter(currency__iexact='ETB').update(currency='USD')


class Migration(migrations.Migration):

    dependencies = [
        ('contracts', '0003_rename_contracts_t_contrac_te_idx_contracts_t_contrac_4340d1_idx_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contract',
            name='currency',
            field=models.CharField(
                default='USD',
                help_text='Currency code',
                max_length=3,
            ),
        ),
        migrations.RunPython(etb_to_usd, migrations.RunPython.noop),
    ]
