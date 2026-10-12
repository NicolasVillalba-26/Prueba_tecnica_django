from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
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

from config.mixins import ContextoPaginacionMixin, MensajeFormularioMixin

from .forms import (
    CategoriaFormulario,
    ContactoFormulario,
    DireccionFormulario,
    EmpresaFormulario,
)
from .models import Categoria, Contacto, Direccion, Empresa


class EliminacionMixin:
    """Confirma eliminaciones por POST y publica un mensaje uniforme."""

    mensaje_exito = 'Registro eliminado correctamente.'

    def form_valid(self, form):
        respuesta = super().form_valid(form)
        messages.success(self.request, self.mensaje_exito)
        return respuesta


class CategoriaListaVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ContextoPaginacionMixin,
    ListView,
):
    permission_required = 'empresas.view_categoria'
    model = Categoria
    template_name = 'empresas/categoria_lista.html'
    context_object_name = 'categorias'
    paginate_by = 10
    nombre_registros = 'categorías'

    def get_queryset(self):
        """Ordena alfabéticamente con un criterio secundario estable."""
        return Categoria.objects.order_by('nombre', 'pk')


class CategoriaCrearVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    MensajeFormularioMixin,
    CreateView,
):
    permission_required = 'empresas.add_categoria'
    model = Categoria
    form_class = CategoriaFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('empresas:categoria_lista')
    extra_context = {
        'titulo_formulario': 'Nueva categoría',
        'ruta_cancelar': 'empresas:categoria_lista',
    }
    mensaje_exito = 'Categoría creada correctamente.'


class CategoriaEditarVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    MensajeFormularioMixin,
    UpdateView,
):
    permission_required = 'empresas.change_categoria'
    model = Categoria
    form_class = CategoriaFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('empresas:categoria_lista')
    extra_context = {
        'titulo_formulario': 'Editar categoría',
        'ruta_cancelar': 'empresas:categoria_lista',
    }
    mensaje_exito = 'Categoría actualizada correctamente.'


class CategoriaEliminarVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    EliminacionMixin,
    DeleteView,
):
    permission_required = 'empresas.delete_categoria'
    model = Categoria
    template_name = 'formularios/confirmar_eliminacion.html'
    success_url = reverse_lazy('empresas:categoria_lista')
    extra_context = {
        'titulo_eliminacion': 'Eliminar categoría',
        'ruta_cancelar': 'empresas:categoria_lista',
    }
    mensaje_exito = 'Categoría eliminada correctamente.'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        cantidad_empresas = self.object.empresas.count()
        if cantidad_empresas:
            contexto['advertencia_relaciones'] = (
                f'Esta categoría está asociada a {cantidad_empresas} empresa(s). '
                'Las empresas no serán eliminadas.'
            )
        return contexto


class EmpresaListaVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ContextoPaginacionMixin,
    ListView,
):
    permission_required = 'empresas.view_empresa'
    model = Empresa
    template_name = 'empresas/empresa_lista.html'
    context_object_name = 'empresas'
    paginate_by = 10
    nombre_registros = 'empresas'
    tipos_permitidos = {'todos', 'clientes', 'proveedores', 'ambos'}

    def get_queryset(self):
        """Combina búsqueda, condición comercial y categoría."""
        empresas = Empresa.objects.all()
        self.termino_busqueda = self.request.GET.get('q', '').strip()
        tipo_solicitado = self.request.GET.get('tipo', 'todos')
        self.tipo_empresa = (
            tipo_solicitado if tipo_solicitado in self.tipos_permitidos
            else 'todos'
        )
        categoria_solicitada = self.request.GET.get('categoria', '').strip()
        try:
            self.categoria_seleccionada = int(categoria_solicitada)
            if self.categoria_seleccionada <= 0:
                raise ValueError
        except (TypeError, ValueError):
            self.categoria_seleccionada = None
            self.categoria_invalida = bool(categoria_solicitada)
        else:
            self.categoria_invalida = False

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

        if self.categoria_invalida:
            empresas = empresas.none()
        elif self.categoria_seleccionada is not None:
            empresas = empresas.filter(
                categorias__pk=self.categoria_seleccionada
            )

        return empresas.distinct().order_by('razon_social', 'pk')

    def get_context_data(self, **kwargs):
        """Conserva los criterios para mostrarlos y mantener la paginación."""
        contexto = super().get_context_data(**kwargs)
        contexto['termino_busqueda'] = self.termino_busqueda
        contexto['tipo_empresa'] = self.tipo_empresa
        contexto['categorias_disponibles'] = Categoria.objects.order_by(
            'nombre', 'pk'
        )
        contexto['categoria_seleccionada'] = self.categoria_seleccionada
        contexto['hay_filtros'] = (
            bool(self.termino_busqueda)
            or self.tipo_empresa != 'todos'
            or self.categoria_seleccionada is not None
            or self.categoria_invalida
        )
        return contexto


class EmpresaDetalleVista(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    permission_required = 'empresas.view_empresa'
    model = Empresa
    template_name = 'empresas/empresa_detalle.html'
    context_object_name = 'empresa'

    def get_queryset(self):
        return Empresa.objects.select_related(
            'usuario_creacion', 'usuario_modificacion'
        ).prefetch_related('categorias', 'contactos')


class EmpresaCrearVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    MensajeFormularioMixin,
    CreateView,
):
    permission_required = 'empresas.add_empresa'
    model = Empresa
    form_class = EmpresaFormulario
    template_name = 'formularios/formulario.html'
    mensaje_exito = 'Empresa creada correctamente.'
    extra_context = {
        'titulo_formulario': 'Nueva empresa',
        'ruta_cancelar': 'empresas:empresa_lista',
    }

    def form_valid(self, form):
        form.instance.usuario_creacion = self.request.user
        form.instance.usuario_modificacion = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('empresas:empresa_detalle', kwargs={'pk': self.object.pk})


class EmpresaEditarVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    MensajeFormularioMixin,
    UpdateView,
):
    permission_required = 'empresas.change_empresa'
    model = Empresa
    form_class = EmpresaFormulario
    template_name = 'formularios/formulario.html'
    mensaje_exito = 'Empresa actualizada correctamente.'
    extra_context = {
        'titulo_formulario': 'Editar empresa',
        'ruta_cancelar': 'empresas:empresa_lista',
    }

    def form_valid(self, form):
        form.instance.usuario_modificacion = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('empresas:empresa_detalle', kwargs={'pk': self.object.pk})


class EmpresaEliminarVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    EliminacionMixin,
    DeleteView,
):
    permission_required = 'empresas.delete_empresa'
    model = Empresa
    template_name = 'formularios/confirmar_eliminacion.html'
    success_url = reverse_lazy('empresas:empresa_lista')
    extra_context = {
        'titulo_eliminacion': 'Eliminar empresa',
        'ruta_cancelar': 'empresas:empresa_lista',
    }
    mensaje_exito = 'Empresa eliminada correctamente.'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['advertencia_relaciones'] = (
            'También se eliminarán sus contactos y las direcciones '
            'dependientes.'
        )
        return contexto


class ContactoListaVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ContextoPaginacionMixin,
    ListView,
):
    permission_required = 'empresas.view_contacto'
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


class ContactoDetalleVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    DetailView,
):
    permission_required = 'empresas.view_contacto'
    model = Contacto
    template_name = 'empresas/contacto_detalle.html'
    context_object_name = 'contacto'

    def get_queryset(self):
        return Contacto.objects.select_related('empresa').prefetch_related(
            'direcciones__ciudad__departamento'
        )


class ContactoCrearVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    MensajeFormularioMixin,
    CreateView,
):
    permission_required = 'empresas.add_contacto'
    model = Contacto
    form_class = ContactoFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('empresas:contacto_lista')
    extra_context = {
        'titulo_formulario': 'Nuevo contacto',
        'ruta_cancelar': 'empresas:contacto_lista',
    }
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
        contexto['url_cancelar'] = reverse(
            'empresas:empresa_detalle', kwargs={'pk': self.empresa.pk}
        )
        return contexto


class ContactoEditarVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    MensajeFormularioMixin,
    UpdateView,
):
    permission_required = 'empresas.change_contacto'
    model = Contacto
    form_class = ContactoFormulario
    template_name = 'formularios/formulario.html'
    mensaje_exito = 'Contacto actualizado correctamente.'
    extra_context = {
        'titulo_formulario': 'Editar contacto',
        'ruta_cancelar': 'empresas:contacto_lista',
    }

    def get_success_url(self):
        return reverse('empresas:contacto_detalle', kwargs={'pk': self.object.pk})


class ContactoEliminarVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    EliminacionMixin,
    DeleteView,
):
    permission_required = 'empresas.delete_contacto'
    model = Contacto
    template_name = 'formularios/confirmar_eliminacion.html'
    success_url = reverse_lazy('empresas:contacto_lista')
    extra_context = {
        'titulo_eliminacion': 'Eliminar contacto',
        'ruta_cancelar': 'empresas:contacto_lista',
    }
    mensaje_exito = 'Contacto eliminado correctamente.'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        if self.object.direcciones.exists():
            contexto['advertencia_relaciones'] = (
                'También se eliminarán sus direcciones.'
            )
        return contexto


class DireccionListaVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    ContextoPaginacionMixin,
    ListView,
):
    permission_required = 'empresas.view_direccion'
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


class DireccionCrearVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    MensajeFormularioMixin,
    CreateView,
):
    permission_required = 'empresas.add_direccion'
    model = Direccion
    form_class = DireccionFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('empresas:direccion_lista')
    extra_context = {
        'titulo_formulario': 'Nueva dirección',
        'ruta_cancelar': 'empresas:direccion_lista',
    }
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
        contexto['subtitulo_formulario'] = (
            f'Contacto: {self.contacto.nombre} {self.contacto.apellido}'
        )
        contexto['url_cancelar'] = reverse(
            'empresas:contacto_detalle', kwargs={'pk': self.contacto.pk}
        )
        return contexto


class DireccionEditarVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    MensajeFormularioMixin,
    UpdateView,
):
    permission_required = 'empresas.change_direccion'
    model = Direccion
    form_class = DireccionFormulario
    template_name = 'formularios/formulario.html'
    success_url = reverse_lazy('empresas:direccion_lista')
    extra_context = {
        'titulo_formulario': 'Editar dirección',
        'ruta_cancelar': 'empresas:direccion_lista',
    }
    mensaje_exito = 'Dirección actualizada correctamente.'


class DireccionEliminarVista(
    LoginRequiredMixin,
    PermissionRequiredMixin,
    EliminacionMixin,
    DeleteView,
):
    permission_required = 'empresas.delete_direccion'
    model = Direccion
    template_name = 'formularios/confirmar_eliminacion.html'
    success_url = reverse_lazy('empresas:direccion_lista')
    extra_context = {
        'titulo_eliminacion': 'Eliminar dirección',
        'ruta_cancelar': 'empresas:direccion_lista',
    }
    mensaje_exito = 'Dirección eliminada correctamente.'
