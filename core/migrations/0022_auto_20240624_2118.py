# Generated by Django 5.0.6 on 2024-06-24 19:18
from __future__ import unicode_literals

from django.db import migrations
from django.utils.text import slugify


def unique_slugify(community, slug):
    Community = community.__class__
    unique_slug = slug
    counter = 1
    while Community.objects.filter(slug=unique_slug).exists():
        unique_slug = f"{slug}-{counter}"
        counter += 1
    return unique_slug


def slugify_name(apps, schema_editor):
    Community = apps.get_model('core', 'Community')
    communities = Community.objects.all()

    for community in communities:
        base_slug = slugify(community.name)
        unique_slug = unique_slugify(community, base_slug)
        community.slug = unique_slug
        community.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0021_alter_community_author'),
    ]

    operations = [
        migrations.RunPython(slugify_name),
    ]