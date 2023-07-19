from django.apps import AppConfig


class BlogConfig(AppConfig):
    """Configuration settings for Blog application."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'blog'
    verbose_name = 'Блог'
