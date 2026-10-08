from django.contrib import admin

from .models import Ciudad, Departamento


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    """Configura el mantenimiento administrativo de departamentos."""

    list_display = ('nombre',)
    search_fields = ('nombre',)
    ordering = ('nombre',)
    list_per_page = 25


@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    """Configura el mantenimiento administrativo de ciudades."""

    list_display = ('nombre', 'departamento')
    search_fields = ('nombre', 'departamento__nombre')
    list_filter = ('departamento',)
    ordering = ('nombre',)
    autocomplete_fields = ('departamento',)
    list_per_page = 25

    def get_queryset(self, request):
        """Carga el departamento para evitar una consulta por cada ciudad."""
        return super().get_queryset(request).select_related('departamento')
