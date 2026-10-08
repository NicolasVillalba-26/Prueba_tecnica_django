from django import forms

from .models import Ciudad, Departamento


class FormularioModeloBootstrap(forms.ModelForm):
    """Aplica estilos Bootstrap a los formularios de ubicaciones."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget, forms.Select):
                campo.widget.attrs['class'] = 'form-select'
            else:
                campo.widget.attrs['class'] = 'form-control'


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
