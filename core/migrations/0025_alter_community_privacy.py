# Generated by Django 5.0.6 on 2024-08-05 18:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_alter_community_privacy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='community',
            name='privacy',
            field=models.CharField(choices=[('10_PUBLIC', 'Public - anyone can view and contribute'), ('20_RESTRICTED', 'Restricted - anyone can view, but only approved users can contribute'), ('30_PRIVATE', 'Private - only approved users can view and contribute')], default='20_RESTRICTED', max_length=15),
        ),
    ]
