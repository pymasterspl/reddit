# Generated by Django 5.0.6 on 2024-06-21 21:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_alter_community_managers_alter_post_managers'),
    ]

    operations = [
        migrations.AddField(
            model_name='community',
            name='slug',
            field=models.SlugField(blank=True, max_length=255, unique=True),
        ),
    ]