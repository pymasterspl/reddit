# Generated by Django 5.0.6 on 2024-08-24 11:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_merge_20240824_1301'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='avatar',
            field=models.ImageField(blank=True, default=None, null=True, upload_to='users_avatars/'),
        ),
    ]
