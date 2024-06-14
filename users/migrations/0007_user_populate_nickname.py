from django.db import migrations


def populate_nickname(apps, schema_editor):
    User = apps.get_model("users", "User")
    for user in User.objects.all():
        if not user.nickname:
            potential_nickname = user.email.split('@')[0]
        potential_suffix = 1
        while User.objects.filter(nickname=potential_nickname).exists():
            potential_nickname = f"{potential_nickname}_{potential_suffix}"
            potential_suffix += 1
        user.nickname = potential_nickname
        user.save()


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_user_nickname'),
    ]

    operations = [
        migrations.RunPython(populate_nickname)
    ]
