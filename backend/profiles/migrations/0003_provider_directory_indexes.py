# Generated manually for public provider directory indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_seed_skill_tags'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['location'], name='profiles_pr_locatio_idx'),
        ),
        migrations.AddIndex(
            model_name='profile',
            index=models.Index(fields=['is_verified'], name='profiles_pr_is_veri_idx'),
        ),
        migrations.AddIndex(
            model_name='serviceproviderprofile',
            index=models.Index(
                fields=['availability_status'],
                name='profiles_sp_availab_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='serviceproviderprofile',
            index=models.Index(fields=['hourly_rate'], name='profiles_sp_hourly__idx'),
        ),
        migrations.AddIndex(
            model_name='serviceproviderprofile',
            index=models.Index(
                fields=['-average_rating'],
                name='profiles_sp_avg_rating_idx',
            ),
        ),
        migrations.AddIndex(
            model_name='serviceproviderprofile',
            index=models.Index(
                fields=['portfolio_visibility', '-average_rating'],
                name='profiles_sp_port_vis_rating_idx',
            ),
        ),
    ]
