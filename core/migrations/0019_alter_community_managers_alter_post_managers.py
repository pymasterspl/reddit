# Generated by Django 5.0.6 on 2024-06-19 16:42

import django.db.models.manager
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0018_alter_post_parent"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="community",
            managers=[
                ("all_objects", django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelManagers(
            name="post",
            managers=[
                ("all_objects", django.db.models.manager.Manager()),
            ],
        ),
    ]
