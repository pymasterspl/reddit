# Generated by Django 5.0.6 on 2024-06-24 19:18
from __future__ import unicode_literals

from django.db import migrations, transaction
from django.utils.text import slugify


def unique_slugify(Community, name):
    base_slug = slugify(name)
    unique_slug = base_slug
    counter = 1
    while Community.all_objects.filter(slug=unique_slug).exists():
        unique_slug = f"{base_slug}-{counter}"
        counter += 1
    return unique_slug


def slugify_name(apps, schema_editor):
    Community = apps.get_model("core", "Community")

    with transaction.atomic():
        for community in Community.all_objects.all():
            if not community.slug:
                community.slug = unique_slugify(Community, community.name)
                community.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_alter_community_author'),
    ]

    operations = [
        migrations.RunPython(slugify_name),
    ]
