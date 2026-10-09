from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from config.mixins import ContextoPaginacionMixin

from .forms import (
    CategoriaFormulario,
    ContactoFormulario,
    DireccionFormulario,
    EmpresaFormulario,
)
from .models import Categoria, Contacto, Direccion, Empresa


class MensajeFormularioMixin:
    """Informa el resultado exitoso de altas y modificaciones."""

    mensaje_exito = 'Registro guardado correctamente.'

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, self.mensaje_exito)
        return respuesta


class EliminacionMixin:
    """Confirma eliminaciones por POST y publica un mensaje uniforme."""

    mensaje_exito = 'Registro eliminado correctamente.'

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, self.mensaje_exito)
        return respuesta


class CategoriaListaVista(LoginRequiredMixin, ContextoPaginacionMixin, ListView):
    model = Categoria
    template_name = 'empresas/categoria_lista.html'
    context_object_name = 'categorias'
    paginate_by = 10
    nombre_registros = 'categorías'

    def get_queryset(self):
        """Ordena alfabéticamente con un criterio secundario estable."""
        return Categoria.objects.order_by('nombre', 'pk')


class CategoriaCrearVista(LoginRequiredMixin, MensajeFormularioMixin, CreateView):
    model = Categoria
    form_class = CategoriaFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('empresas:categoria_lista')
    extra_context = {'titulo_formulario': 'Nueva categoría', 'ruta_cancelar': 'empresas:categoria_lista'}
    mensaje_exito = 'Categoría creada correctamente.'


class CategoriaEditarVista(LoginRequiredMixin, MensajeFormularioMixin, UpdateView):
    model = Categoria
    form_class = CategoriaFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('empresas:categoria_lista')
    extra_context = {'titulo_formulario': 'Editar categoría', 'ruta_cancelar': 'empresas:categoria_lista'}
    mensaje_exito = 'Categoría actualizada correctamente.'


class CategoriaEliminarVista(LoginRequiredMixin, EliminacionMixin, DeleteView):
    model = Categoria
    template_name = 'formularios/confirmar_eliminacion.html'
    success_url = reverse_lazy('empresas:categoria_lista')
    extra_context = {'titulo_eliminacion': 'Eliminar categoría', 'ruta_cancelar': 'empresas:categoria_lista'}
    mensaje_exito = 'Categoría eliminada correctamente.'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['advertencia_relaciones'] = (
            f'Esta categoría está asociada a {self.object.empresas.count()} empresa(s). '
            'Las empresas no serán eliminadas.'
        )
        return contexto


class EmpresaListaVista(LoginRequiredMixin, ContextoPaginacionMixin, ListView):
    model = Empresa
    template_name = 'empresas/empresa_lista.html'
    context_object_name = 'empresas'
    paginate_by = 10
    nombre_registros = 'empresas'
    tipos_permitidos = {'todos', 'clientes', 'proveedores', 'ambos'}

    def get_queryset(self):
        """Filtra empresas por razón social, RUC o correo electrónico."""
        empresas = Empresa.objects.prefetch_related('categorias')
        self.termino_busqueda = self.request.GET.get('q', '').strip()
        tipo_solicitado = self.request.GET.get('tipo', 'todos')
        self.tipo_empresa = (
            tipo_solicitado if tipo_solicitado in self.tipos_permitidos
            else 'todos'
        )

        if self.termino_busqueda:
            empresas = empresas.filter(
                Q(razon_social__icontains=self.termino_busqueda)
                | Q(ruc__icontains=self.termino_busqueda)
                | Q(email__icontains=self.termino_busqueda)
            )

        if self.tipo_empresa == 'clientes':
            empresas = empresas.filter(es_cliente=True)
        elif self.tipo_empresa == 'proveedores':
            empresas = empresas.filter(es_proveedor=True)
        elif self.tipo_empresa == 'ambos':
            empresas = empresas.filter(es_cliente=True, es_proveedor=True)

        return empresas.order_by('razon_social', 'pk')

    def get_context_data(self, **kwargs):
        """Conserva los criterios para mostrarlos y mantener la paginación."""
        contexto = super().get_context_data(**kwargs)
        contexto['termino_busqueda'] = self.termino_busqueda
        contexto['tipo_empresa'] = self.tipo_empresa
        contexto['hay_filtros'] = (
            bool(self.termino_busqueda) or self.tipo_empresa != 'todos'
        )
        return contexto


class EmpresaDetalleVista(LoginRequiredMixin, DetailView):
    model = Empresa
    template_name = 'empresas/empresa_detalle.html'
    context_object_name = 'empresa'

    def get_queryset(self):
        return Empresa.objects.select_related(
            'usuario_creacion', 'usuario_modificacion'
        ).prefetch_related('categorias', 'contactos')


class EmpresaCrearVista(LoginRequiredMixin, MensajeFormularioMixin, CreateView):
    model = Empresa
    form_class = EmpresaFormulario
    template_name = 'formularios/formulario.html'
    mensaje_exito = 'Empresa creada correctamente.'
    extra_context = {'titulo_formulario': 'Nueva empresa', 'ruta_cancelar': 'empresas:empresa_lista'}

    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        form.instance.usuario_modificacion = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('empresas:empresa_detalle', kwargs={'pk': self.object.pk})


class EmpresaEditarVista(LoginRequiredMixin, MensajeFormularioMixin, UpdateView):
    model = Empresa
    form_class = EmpresaFormulario
    template_name = 'formularios/formulario.html'
    mensaje_exito = 'Empresa actualizada correctamente.'
    extra_context = {'titulo_formulario': 'Editar empresa', 'ruta_cancelar': 'empresas:empresa_lista'}

    def form_valid(self, form):
        form.instance.usuario_modificacion = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('empresas:empresa_detalle', kwargs={'pk': self.object.pk})


class EmpresaEliminarVista(LoginRequiredMixin, EliminacionMixin, DeleteView):
    model = Empresa
    template_name = 'formularios/confirmar_eliminacion.html'
    success_url = reverse_lazy('empresas:empresa_lista')
    extra_context = {'titulo_eliminacion': 'Eliminar empresa', 'ruta_cancelar': 'empresas:empresa_lista'}
    mensaje_exito = 'Empresa eliminada correctamente.'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['advertencia_relaciones'] = (
            'También se eliminarán sus contactos y las direcciones dependientes.'
        )
        return contexto


class ContactoListaVista(LoginRequiredMixin, ContextoPaginacionMixin, ListView):
    model = Contacto
    template_name = 'empresas/contacto_lista.html'
    context_object_name = 'contactos'
    paginate_by = 10
    nombre_registros = 'contactos'

    def get_queryset(self):
        """Obtiene contactos y sus empresas con un orden estable."""
        return Contacto.objects.select_related('empresa').order_by(
            'apellido', 'nombre', 'pk'
        )


class ContactoDetalleVista(LoginRequiredMixin, DetailView):
    model = Contacto
    template_name = 'empresas/contacto_detalle.html'
    context_object_name = 'contacto'

    def get_queryset(self):
        return Contacto.objects.select_related('empresa').prefetch_related(
            'direcciones__ciudad__departamento'
        )


class ContactoCrearVista(LoginRequiredMixin, MensajeFormularioMixin, CreateView):
    model = Contacto
    form_class = ContactoFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('empresas:contacto_lista')
    extra_context = {'titulo_formulario': 'Nuevo contacto', 'ruta_cancelar': 'empresas:contacto_lista'}
    mensaje_exito = 'Contacto creado correctamente.'


class ContactoEmpresaCrearVista(ContactoCrearVista):
    """Crea un contacto fijando la empresa indicada por la ruta."""

    def dispatch(self, request, *args, **kwargs):
        self.empresa = get_object_or_404(Empresa, pk=kwargs['empresa_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        formulario = super().get_form(form_class)
        formulario.fields.pop('empresa', None)
        return formulario

    def form_valid(self, form):
        form.instance.empresa = self.empresa
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('empresas:empresa_detalle', kwargs={'pk': self.empresa.pk})

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['subtitulo_formulario'] = f'Empresa: {self.empresa.razon_social}'
        contexto['url_cancelar'] = reverse('empresas:empresa_detalle', kwargs={'pk': self.empresa.pk})
        return contexto


class ContactoEditarVista(LoginRequiredMixin, MensajeFormularioMixin, UpdateView):
    model = Contacto
    form_class = ContactoFormulario
    template_name = 'formularios/formulario.html'
    mensaje_exito = 'Contacto actualizado correctamente.'
    extra_context = {'titulo_formulario': 'Editar contacto', 'ruta_cancelar': 'empresas:contacto_lista'}

    def get_success_url(self):
        return reverse('empresas:contacto_detalle', kwargs={'pk': self.object.pk})


class ContactoEliminarVista(LoginRequiredMixin, EliminacionMixin, DeleteView):
    model = Contacto
    template_name = 'formularios/confirmar_eliminacion.html'
    success_url = reverse_lazy('empresas:contacto_lista')
    extra_context = {'titulo_eliminacion': 'Eliminar contacto', 'ruta_cancelar': 'empresas:contacto_lista'}
    mensaje_exito = 'Contacto eliminado correctamente.'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['advertencia_relaciones'] = 'También se eliminarán sus direcciones.'
        return contexto


class DireccionListaVista(LoginRequiredMixin, ContextoPaginacionMixin, ListView):
    model = Direccion
    template_name = 'empresas/direccion_lista.html'
    context_object_name = 'direcciones'
    paginate_by = 10
    nombre_registros = 'direcciones'

    def get_queryset(self):
        """Obtiene las relaciones visibles y conserva un orden determinista."""
        return Direccion.objects.select_related(
            'contacto', 'contacto__empresa', 'ciudad', 'ciudad__departamento'
        ).order_by('pk')


class DireccionCrearVista(LoginRequiredMixin, MensajeFormularioMixin, CreateView):
    model = Direccion
    form_class = DireccionFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('empresas:direccion_lista')
    extra_context = {'titulo_formulario': 'Nueva dirección', 'ruta_cancelar': 'empresas:direccion_lista'}
    mensaje_exito = 'Dirección creada correctamente.'


class DireccionContactoCrearVista(DireccionCrearVista):
    """Crea una dirección fijando el contacto indicado por la ruta."""

    def dispatch(self, request, *args, **kwargs):
        self.contacto = get_object_or_404(Contacto, pk=kwargs['contacto_pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        formulario = super().get_form(form_class)
        formulario.fields.pop('contacto', None)
        return formulario

    def form_valid(self, form):
        form.instance.contacto = self.contacto
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('empresas:contacto_detalle', kwargs={'pk': self.contacto.pk})

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['subtitulo_formulario'] = f'Contacto: {self.contacto.nombre} {self.contacto.apellido}'
        contexto['url_cancelar'] = reverse('empresas:contacto_detalle', kwargs={'pk': self.contacto.pk})
        return contexto


class DireccionEditarVista(LoginRequiredMixin, MensajeFormularioMixin, UpdateView):
    model = Direccion
    form_class = DireccionFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('empresas:direccion_lista')
    extra_context = {'titulo_formulario': 'Editar dirección', 'ruta_cancelar': 'empresas:direccion_lista'}
    mensaje_exito = 'Dirección actualizada correctamente.'


class DireccionEliminarVista(LoginRequiredMixin, EliminacionMixin, DeleteView):
    model = Direccion
    template_name = 'formularios/confirmar_eliminacion.html'
    success_url = reverse_lazy('empresas:direccion_lista')
    extra_context = {'titulo_eliminacion': 'Eliminar dirección', 'ruta_cancelar': 'empresas:direccion_lista'}
    mensaje_exito = 'Dirección eliminada correctamente.'
