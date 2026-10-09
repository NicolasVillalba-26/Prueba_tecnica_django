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
