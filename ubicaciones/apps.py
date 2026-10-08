from django.apps import AppConfig


class UbicacionesConfig(AppConfig):
    """Configura la aplicación que administra departamentos y ciudades."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ubicaciones'
    verbose_name = 'Ubicaciones'
