# Generated by Django 5.0.6 on 2024-07-29 19:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_community_is_18_plus_community_privacy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='community',
            name='privacy',
            field=models.CharField(choices=[('PUBLIC', 'Public - anyone can view and contribute'), ('RESTRICTED', 'Restricted - anyone can view, but only approved users can contribute'), ('PRIVATE', 'Private - only approved users can view and contribute')], default='PUBLIC', max_length=10),
        ),
    ]
