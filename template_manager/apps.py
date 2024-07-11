from django.apps import AppConfig

class TemplateManagerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'template_manager'

    def ready(self):
        import template_manager.signals  # Import signals module
