# Generated by Django 5.0.6 on 2024-06-30 11:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0022_postreport'),
    ]

    operations = [
        migrations.AddField(
            model_name='postreport',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
