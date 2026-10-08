from django.urls import path

from .views import (
    CiudadCrearVista, CiudadEditarVista, CiudadEliminarVista, CiudadListaVista,
    DepartamentoCrearVista, DepartamentoEditarVista,
    DepartamentoEliminarVista, DepartamentoListaVista,
)

app_name = 'ubicaciones'

urlpatterns = [
    path('departamentos/', DepartamentoListaVista.as_view(), name='departamento_lista'),
    path('departamentos/nuevo/', DepartamentoCrearVista.as_view(), name='departamento_crear'),
    path('departamentos/<int:pk>/editar/', DepartamentoEditarVista.as_view(), name='departamento_editar'),
    path('departamentos/<int:pk>/eliminar/', DepartamentoEliminarVista.as_view(), name='departamento_eliminar'),
    path('ciudades/', CiudadListaVista.as_view(), name='ciudad_lista'),
    path('ciudades/nueva/', CiudadCrearVista.as_view(), name='ciudad_crear'),
    path('ciudades/<int:pk>/editar/', CiudadEditarVista.as_view(), name='ciudad_editar'),
    path('ciudades/<int:pk>/eliminar/', CiudadEliminarVista.as_view(), name='ciudad_eliminar'),
]
