# from django.apps import AppConfig


# class JobsConfig(AppConfig):
#     name = "apps.jobs"
#     default_auto_field = "django.db.models.BigAutoField"
#     verbose_name = "Content Generation Jobs"

#     def ready(self) -> None:
#         # Register signal handlers — must be imported here so receivers
#         # are connected before the first request arrives.
#         import apps.jobs.signals  # noqa: F401











from django.apps import AppConfig


class JobsConfig(AppConfig):
    name = "instaAutoAI.apps.jobs"  # <-- Full dotted path
    label = "jobs"  # <-- Short label for DB tables
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = "Content Generation Jobs"

    def ready(self) -> None:
        # Register signal handlers — must be imported here so receivers
        # are connected before the first request arrives.
        import instaAutoAI.apps.jobs.signals  # noqa: F401