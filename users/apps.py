from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self: "UsersConfig") -> None:
        from . import signals  # noqa: F401
