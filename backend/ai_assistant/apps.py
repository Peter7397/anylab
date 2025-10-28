from django.apps import AppConfig


class AiAssistantConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_assistant'
    
    def ready(self):
        """Import signals when app is ready"""
        import ai_assistant.signals  # noqa