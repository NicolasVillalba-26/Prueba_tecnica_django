from django.urls import path

from .views import (
    CategoriaCrearVista, CategoriaEditarVista, CategoriaEliminarVista,
    CategoriaListaVista, ContactoCrearVista, ContactoDetalleVista,
    ContactoEditarVista, ContactoEliminarVista, ContactoEmpresaCrearVista,
    ContactoListaVista, DireccionContactoCrearVista, DireccionCrearVista,
    DireccionEditarVista, DireccionEliminarVista, DireccionListaVista,
    EmpresaCrearVista, EmpresaDetalleVista, EmpresaEditarVista,
    EmpresaEliminarVista, EmpresaListaVista,
)

app_name = 'empresas'

urlpatterns = [
    path('', EmpresaListaVista.as_view(), name='empresa_lista'),
    path('nueva/', EmpresaCrearVista.as_view(), name='empresa_crear'),
    path('<int:pk>/', EmpresaDetalleVista.as_view(), name='empresa_detalle'),
    path('<int:pk>/editar/', EmpresaEditarVista.as_view(), name='empresa_editar'),
    path('<int:pk>/eliminar/', EmpresaEliminarVista.as_view(), name='empresa_eliminar'),
    path('<int:empresa_pk>/contactos/nuevo/', ContactoEmpresaCrearVista.as_view(), name='empresa_contacto_crear'),
    path('categorias/', CategoriaListaVista.as_view(), name='categoria_lista'),
    path('categorias/nueva/', CategoriaCrearVista.as_view(), name='categoria_crear'),
    path('categorias/<int:pk>/editar/', CategoriaEditarVista.as_view(), name='categoria_editar'),
    path('categorias/<int:pk>/eliminar/', CategoriaEliminarVista.as_view(), name='categoria_eliminar'),
    path('contactos/', ContactoListaVista.as_view(), name='contacto_lista'),
    path('contactos/nuevo/', ContactoCrearVista.as_view(), name='contacto_crear'),
    path('contactos/<int:pk>/', ContactoDetalleVista.as_view(), name='contacto_detalle'),
    path('contactos/<int:pk>/editar/', ContactoEditarVista.as_view(), name='contacto_editar'),
    path('contactos/<int:pk>/eliminar/', ContactoEliminarVista.as_view(), name='contacto_eliminar'),
    path('contactos/<int:contacto_pk>/direcciones/nueva/', DireccionContactoCrearVista.as_view(), name='contacto_direccion_crear'),
    path('direcciones/', DireccionListaVista.as_view(), name='direccion_lista'),
    path('direcciones/nueva/', DireccionCrearVista.as_view(), name='direccion_crear'),
    path('direcciones/<int:pk>/editar/', DireccionEditarVista.as_view(), name='direccion_editar'),
    path('direcciones/<int:pk>/eliminar/', DireccionEliminarVista.as_view(), name='direccion_eliminar'),
]
