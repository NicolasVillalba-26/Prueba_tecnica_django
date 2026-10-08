from django.contrib import admin

from .models import Categoria, Contacto, Direccion, Empresa


class ContactoEnLinea(admin.TabularInline):
    """Permite mantener contactos desde la ficha de una empresa."""

    model = Contacto
    extra = 0
    fields = ('nombre', 'apellido', 'email', 'telefono', 'cargo')
    show_change_link = True


class DireccionEnLinea(admin.TabularInline):
    """Permite mantener direcciones desde la ficha de un contacto."""

    model = Direccion
    extra = 0
    autocomplete_fields = ('ciudad',)
    show_change_link = True


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    """Configura la búsqueda y listado administrativo de categorías."""

    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre', 'descripcion')
    ordering = ('nombre',)
    list_per_page = 25


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    """Administra empresas y asigna automáticamente su auditoría."""

    list_display = (
        'razon_social',
        'ruc',
        'email',
        'es_cliente',
        'es_proveedor',
        'activo',
        'fecha_modificacion',
    )
    search_fields = ('razon_social', 'ruc', 'email', 'telefono')
    list_filter = ('es_cliente', 'es_proveedor', 'activo', 'categorias')
    ordering = ('razon_social',)
    readonly_fields = (
        'fecha_creacion',
        'fecha_modificacion',
        'usuario_creacion',
        'usuario_modificacion',
    )
    filter_horizontal = ('categorias',)
    list_per_page = 25
    inlines = (ContactoEnLinea,)

    def save_model(self, request, obj, form, change):
        """Asigna el usuario autenticado sin exponer campos manipulables."""
        if not change or obj.usuario_creacion_id is None:
            obj.usuario_creacion = request.user
        obj.usuario_modificacion = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        """Evita consultas adicionales al mostrar usuarios de auditoría."""
        return super().get_queryset(request).select_related(
            'usuario_creacion',
            'usuario_modificacion',
        )


@admin.register(Contacto)
class ContactoAdmin(admin.ModelAdmin):
    """Configura el mantenimiento administrativo de contactos."""

    list_display = ('nombre', 'apellido', 'empresa', 'cargo', 'email', 'telefono')
    search_fields = (
        'nombre',
        'apellido',
        'email',
        'empresa__razon_social',
        'empresa__ruc',
    )
    list_filter = ('empresa',)
    ordering = ('apellido', 'nombre')
    autocomplete_fields = ('empresa',)
    list_per_page = 25
    inlines = (DireccionEnLinea,)

    def get_queryset(self, request):
        """Carga la empresa junto con cada contacto listado."""
        return super().get_queryset(request).select_related('empresa')


@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    """Configura el mantenimiento administrativo de direcciones."""

    list_display = ('direccion', 'tipo', 'contacto', 'ciudad', 'codigo_postal')
    search_fields = (
        'direccion',
        'codigo_postal',
        'contacto__nombre',
        'contacto__apellido',
        'ciudad__nombre',
    )
    list_filter = ('tipo', 'ciudad__departamento')
    ordering = ('contacto', 'tipo', 'direccion')
    autocomplete_fields = ('contacto', 'ciudad')
    list_per_page = 25

    def get_queryset(self, request):
        """Carga relaciones usadas por las columnas del listado."""
        return super().get_queryset(request).select_related(
            'contacto',
            'contacto__empresa',
            'ciudad',
            'ciudad__departamento',
        )
