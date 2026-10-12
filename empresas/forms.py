from django import forms

from config.mixins import FormularioModeloBootstrap

from .models import Categoria, Contacto, Direccion, Empresa


class CategoriaFormulario(FormularioModeloBootstrap):
    """Captura los datos editables de una categoría."""

    class Meta:
        model = Categoria
        fields = ('nombre', 'descripcion')
        widgets = {'descripcion': forms.Textarea(attrs={'rows': 4})}


class EmpresaFormulario(FormularioModeloBootstrap):
    """Gestiona empresas sin exponer sus campos de auditoría."""

    class Meta:
        model = Empresa
        fields = (
            'razon_social', 'ruc', 'email', 'telefono',
            'es_cliente', 'es_proveedor', 'activo', 'categorias',
        )
        widgets = {'categorias': forms.CheckboxSelectMultiple()}
        error_messages = {
            'ruc': {
                'required': 'El RUC es obligatorio.',
                'unique': 'El RUC ya se encuentra registrado.',
            },
        }


class ContactoFormulario(FormularioModeloBootstrap):
    """Gestiona contactos y su empresa asociada."""

    class Meta:
        model = Contacto
        fields = ('empresa', 'nombre', 'apellido', 'email', 'telefono', 'cargo')


class DireccionFormulario(FormularioModeloBootstrap):
    """Gestiona direcciones con tipos y relaciones válidas del modelo."""

    class Meta:
        model = Direccion
        fields = ('contacto', 'direccion', 'codigo_postal', 'tipo', 'ciudad')
