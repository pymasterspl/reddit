# Generated by Django 5.0.6 on 2024-07-01 15:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_profile_usersettings_alter_user_nickname_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='avatar',
            field=models.ImageField(blank=True, default=None, null=True, upload_to='users_avatars/'),
        ),
    ]
