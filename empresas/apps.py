from django.apps import AppConfig


class EmpresasConfig(AppConfig):
    """Configura la aplicación responsable de la gestión empresarial."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'empresas'
    verbose_name = 'Empresas'
