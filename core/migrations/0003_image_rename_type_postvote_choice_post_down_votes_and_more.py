# Generated by Django 5.0.6 on 2024-05-22 21:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_tag_created_at"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Image",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("image", models.ImageField(upload_to="")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.RenameField(
            model_name="postvote",
            old_name="type",
            new_name="choice",
        ),
        migrations.AddField(
            model_name="post",
            name="down_votes",
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name="post",
            name="parent",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_query_name="children",
                to="core.post",
            ),
        ),
        migrations.AddField(
            model_name="post",
            name="up_votes",
            field=models.IntegerField(default=0),
        ),
        migrations.RemoveField(
            model_name="post",
            name="image",
        ),
        migrations.AlterField(
            model_name="post",
            name="version",
            field=models.CharField(
                help_text="Hash of the title + content to prevent overwriting already saved post",
                max_length=32,
            ),
        ),
        migrations.RemoveField(
            model_name="postvote",
            name="user",
        ),
        migrations.AddField(
            model_name="post",
            name="image",
            field=models.ManyToManyField(
                blank=True, related_name="posts", to="core.image"
            ),
        ),
        migrations.AddField(
            model_name="postvote",
            name="user",
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="post_votes",
                to=settings.AUTH_USER_MODEL,
            ),
            preserve_default=False,
        ),
    ]
