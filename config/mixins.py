from django import forms
from django.contrib import messages


class FormularioModeloBootstrap(forms.ModelForm):
    """Aplica clases Bootstrap coherentes a los campos de un ModelForm."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            if isinstance(campo.widget, forms.CheckboxSelectMultiple):
                # CheckboxSelectMultiple reutiliza ``attrs`` tanto en el
                # contenedor como en cada opción. Aplicar ``form-check-input``
                # aquí hace que Bootstrap dibuje un checkbox sobre el grupo.
                continue
            if isinstance(campo.widget, forms.CheckboxInput):
                campo.widget.attrs['class'] = 'form-check-input'
            elif isinstance(
                campo.widget,
                (forms.SelectMultiple, forms.Select),
            ):
                campo.widget.attrs['class'] = 'form-select'
            else:
                campo.widget.attrs['class'] = 'form-control'


class MensajeFormularioMixin:
    """Informa el resultado exitoso de altas y modificaciones."""

    mensaje_exito = 'Registro guardado correctamente.'

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, self.mensaje_exito)
        return respuesta


class ContextoPaginacionMixin:
    """Prepara enlaces paginados conservando los parámetros GET activos."""

    nombre_registros = 'registros'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        parametros_paginacion = self.request.GET.copy()
        parametros_paginacion.pop('page', None)
        contexto['parametros_paginacion'] = parametros_paginacion.urlencode()
        contexto['nombre_registros'] = self.nombre_registros

        if contexto['is_paginated']:
            contexto['rango_paginas'] = contexto[
                'paginator'
            ].get_elided_page_range(
                contexto['page_obj'].number,
                on_each_side=2,
                on_ends=1,
            )
            contexto['indicador_elipsis'] = contexto['paginator'].ELLIPSIS
        return contexto
