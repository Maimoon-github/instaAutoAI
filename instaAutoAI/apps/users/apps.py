from django.apps import AppConfig


class UsersConfig(AppConfig):
    name = "apps.users"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = "Users"
    # No signals to import in ready() — users app has none.