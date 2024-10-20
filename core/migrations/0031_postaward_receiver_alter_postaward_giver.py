# Generated by Django 5.1 on 2024-09-30 23:08

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0030_alter_postaward_unique_together_postaward_giver_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='postaward',
            name='receiver',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='awards_received', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='postaward',
            name='giver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='awards_given', to=settings.AUTH_USER_MODEL),
        ),
    ]
