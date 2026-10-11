from django.db import migrations, models


def etb_to_usd(apps, schema_editor):
    Payment = apps.get_model('payments', 'Payment')
    Payment.objects.filter(currency__iexact='ETB').update(currency='USD')


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0003_alter_payment_milestone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='currency',
            field=models.CharField(
                default='USD',
                help_text='Currency code',
                max_length=3,
            ),
        ),
        migrations.RunPython(etb_to_usd, migrations.RunPython.noop),
    ]
