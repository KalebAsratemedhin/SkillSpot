# Generated data migration: seed default skill tags.

from django.db import migrations


def seed_skill_tags(apps, schema_editor):
    Tag = apps.get_model('profiles', 'Tag')
    skills = [
        'Plumbing',
        'Electrical',
        'Gardening',
        'Tutoring',
        'Cleaning',
        'Carpentry',
        'Painting',
        'Moving & Delivery',
        'Pet Care',
        'Childcare',
        'Landscaping',
        'HVAC',
        'Appliance Repair',
        'Handyman',
        'Photography',
        'Event Planning',
        'Personal Training',
        'Tutoring - Math',
        'Tutoring - Language',
        'Housekeeping',
        'Lawn Care',
        'Roofing',
        'Fencing',
        'Pest Control',
        'Locksmith',
    ]
    for name in skills:
        Tag.objects.get_or_create(
            name=name,
            defaults={'category': 'SKILL'}
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_skill_tags, noop),
    ]

