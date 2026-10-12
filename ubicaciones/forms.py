from config.mixins import FormularioModeloBootstrap

from .models import Ciudad, Departamento


class DepartamentoFormulario(FormularioModeloBootstrap):
    """Gestiona el nombre único de un departamento."""

    class Meta:
        model = Departamento
        fields = ('nombre',)


class CiudadFormulario(FormularioModeloBootstrap):
    """Gestiona una ciudad y su departamento."""

    class Meta:
        model = Ciudad
        fields = ('nombre', 'departamento')
