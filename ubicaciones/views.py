from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.deletion import ProtectedError
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from config.mixins import ContextoPaginacionMixin

from .forms import CiudadFormulario, DepartamentoFormulario
from .models import Ciudad, Departamento


class MensajeFormularioMixin:
    """Informa el resultado exitoso de altas y modificaciones."""

    mensaje_exito = 'Registro guardado correctamente.'

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, self.mensaje_exito)
        return respuesta


class EliminacionProtegidaMixin:
    """Convierte una relación protegida en un mensaje comprensible."""

    mensaje_exito = 'Registro eliminado correctamente.'
    mensaje_protegido = 'No es posible eliminar el registro porque está siendo utilizado.'

    def form_valid(self, form):
        self.object = self.get_object()
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(self.request, self.mensaje_protegido)
            return redirect(self.get_success_url())
        messages.success(self.request, self.mensaje_exito)
        return redirect(self.get_success_url())


class DepartamentoListaVista(LoginRequiredMixin, ListView):
    model = Departamento
    template_name = 'ubicaciones/departamento_lista.html'
    context_object_name = 'departamentos'
    paginate_by = 20


class DepartamentoCrearVista(LoginRequiredMixin, MensajeFormularioMixin, CreateView):
    model = Departamento
    form_class = DepartamentoFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('ubicaciones:departamento_lista')
    extra_context = {'titulo_formulario': 'Nuevo departamento', 'ruta_cancelar': 'ubicaciones:departamento_lista'}
    mensaje_exito = 'Departamento creado correctamente.'


class DepartamentoEditarVista(LoginRequiredMixin, MensajeFormularioMixin, UpdateView):
    model = Departamento
    form_class = DepartamentoFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('ubicaciones:departamento_lista')
    extra_context = {'titulo_formulario': 'Editar departamento', 'ruta_cancelar': 'ubicaciones:departamento_lista'}
    mensaje_exito = 'Departamento actualizado correctamente.'


class DepartamentoEliminarVista(LoginRequiredMixin, EliminacionProtegidaMixin, DeleteView):
    model = Departamento
    template_name = 'formularios/confirmar_eliminacion.html'
    success_url = reverse_lazy('ubicaciones:departamento_lista')
    extra_context = {'titulo_eliminacion': 'Eliminar departamento', 'ruta_cancelar': 'ubicaciones:departamento_lista'}
    mensaje_exito = 'Departamento eliminado correctamente.'
    mensaje_protegido = 'No es posible eliminar el departamento porque tiene ciudades asociadas.'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        if self.object.ciudades.exists():
            contexto['advertencia_relaciones'] = 'Este departamento tiene ciudades asociadas y no puede eliminarse.'
        return contexto


class CiudadListaVista(LoginRequiredMixin, ContextoPaginacionMixin, ListView):
    model = Ciudad
    template_name = 'ubicaciones/ciudad_lista.html'
    context_object_name = 'ciudades'
    paginate_by = 10
    nombre_registros = 'ciudades'

    def get_queryset(self):
        """Obtiene cada departamento y aplica un orden estable."""
        return Ciudad.objects.select_related('departamento').order_by(
            'nombre', 'departamento__nombre', 'pk'
        )


class CiudadCrearVista(LoginRequiredMixin, MensajeFormularioMixin, CreateView):
    model = Ciudad
    form_class = CiudadFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('ubicaciones:ciudad_lista')
    extra_context = {'titulo_formulario': 'Nueva ciudad', 'ruta_cancelar': 'ubicaciones:ciudad_lista'}
    mensaje_exito = 'Ciudad creada correctamente.'


class CiudadEditarVista(LoginRequiredMixin, MensajeFormularioMixin, UpdateView):
    model = Ciudad
    form_class = CiudadFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('ubicaciones:ciudad_lista')
    extra_context = {'titulo_formulario': 'Editar ciudad', 'ruta_cancelar': 'ubicaciones:ciudad_lista'}
    mensaje_exito = 'Ciudad actualizada correctamente.'


class CiudadEliminarVista(LoginRequiredMixin, EliminacionProtegidaMixin, DeleteView):
    model = Ciudad
    template_name = 'formularios/confirmar_eliminacion.html'
    success_url = reverse_lazy('ubicaciones:ciudad_lista')
    extra_context = {'titulo_eliminacion': 'Eliminar ciudad', 'ruta_cancelar': 'ubicaciones:ciudad_lista'}
    mensaje_exito = 'Ciudad eliminada correctamente.'
    mensaje_protegido = 'No es posible eliminar la ciudad porque tiene direcciones asociadas.'
