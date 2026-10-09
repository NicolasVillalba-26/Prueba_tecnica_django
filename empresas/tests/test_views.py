from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from empresas.admin import EmpresaAdmin
from empresas.models import Categoria, Contacto, Direccion, Empresa
from ubicaciones.models import Ciudad, Departamento


class EmpresaAdminPruebas(TestCase):
    """Verifica la asignación segura de auditoría desde Django Admin."""

    def setUp(self):
        self.fabrica = RequestFactory()
        self.administrador_modelo = EmpresaAdmin(Empresa, admin.site)
        self.usuario = get_user_model().objects.create_superuser(
            username='administrador',
            email='admin@example.com',
            password='clave-segura-pruebas',
        )

    def test_asigna_usuarios_al_crear_empresa(self):
        solicitud = self.fabrica.post('/admin/empresas/empresa/add/')
        solicitud.user = self.usuario
        empresa = Empresa(
            razon_social='Empresa Auditada S.A.',
            ruc='80000100-0',
            email='auditada@example.com',
            telefono='021 555 100',
            es_cliente=True,
        )

        self.administrador_modelo.save_model(
            solicitud,
            empresa,
            form=None,
            change=False,
        )

        self.assertEqual(empresa.usuario_creacion, self.usuario)
        self.assertEqual(empresa.usuario_modificacion, self.usuario)


class CrudEmpresasPruebas(TestCase):
    """Verifica operaciones web, relaciones, auditoría y protección de rutas."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='operador', password='Clave-segura-2026'
        )
        cls.otro_usuario = get_user_model().objects.create_user(username='creador')
        cls.departamento = Departamento.objects.create(nombre='Central')
        cls.ciudad = Ciudad.objects.create(nombre='Asunción', departamento=cls.departamento)
        cls.categoria = Categoria.objects.create(nombre='Servicios', descripcion='Servicios generales')
        cls.empresa = Empresa.objects.create(
            razon_social='Empresa Inicial S.A.', ruc='80001000-0',
            email='inicial@example.com', telefono='021 100 000',
            es_cliente=True, usuario_creacion=cls.otro_usuario,
            usuario_modificacion=cls.otro_usuario,
        )
        cls.contacto = Contacto.objects.create(
            empresa=cls.empresa, nombre='Ana', apellido='Gómez',
            email='ana@example.com', telefono='0981 100 000', cargo='Gerente',
        )
        cls.direccion = Direccion.objects.create(
            contacto=cls.contacto, direccion='Avenida Principal 100',
            codigo_postal='1209', tipo=Direccion.Tipo.LABORAL, ciudad=cls.ciudad,
        )

    def setUp(self):
        self.client.force_login(self.usuario)

    def test_listados_requieren_autenticacion(self):
        self.client.logout()
        rutas = (
            'empresa_lista', 'contacto_lista', 'direccion_lista', 'categoria_lista',
        )
        for nombre in rutas:
            with self.subTest(nombre=nombre):
                respuesta = self.client.get(reverse(f'empresas:{nombre}'))
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn(reverse('login'), respuesta.url)

    def test_crear_empresa_guarda_categorias_y_auditoria(self):
        respuesta = self.client.post(reverse('empresas:empresa_crear'), {
            'razon_social': 'Nueva Empresa S.A.', 'ruc': '80001001-0',
            'email': 'nueva@example.com', 'telefono': '021 100 001',
            'es_cliente': 'on', 'activo': 'on',
            'categorias': [self.categoria.pk],
            'usuario_creacion': self.otro_usuario.pk,
        })

        empresa = Empresa.objects.get(ruc='80001001-0')
        self.assertRedirects(respuesta, reverse('empresas:empresa_detalle', args=[empresa.pk]))
        self.assertEqual(empresa.usuario_creacion, self.usuario)
        self.assertEqual(empresa.usuario_modificacion, self.usuario)
        self.assertEqual(list(empresa.categorias.all()), [self.categoria])


    def test_editar_empresa_conserva_usuario_creacion(self):
        respuesta = self.client.post(reverse('empresas:empresa_editar', args=[self.empresa.pk]), {
            'razon_social': 'Empresa Modificada S.A.', 'ruc': self.empresa.ruc,
            'email': self.empresa.email, 'telefono': self.empresa.telefono,
            'es_proveedor': 'on', 'activo': 'on',
        })

        self.assertEqual(respuesta.status_code, 302)
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.usuario_creacion, self.otro_usuario)
        self.assertEqual(self.empresa.usuario_modificacion, self.usuario)
        self.assertTrue(self.empresa.es_proveedor)

    def test_no_elimina_empresa_mediante_get(self):
        respuesta = self.client.get(reverse('empresas:empresa_eliminar', args=[self.empresa.pk]))

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(Empresa.objects.filter(pk=self.empresa.pk).exists())

    def test_elimina_empresa_y_dependencias_mediante_post(self):
        empresa = Empresa.objects.create(
            razon_social='Temporal S.A.', ruc='80001002-0',
            email='temporal@example.com', telefono='021 100 002', es_cliente=True,
        )
        contacto = Contacto.objects.create(
            empresa=empresa, nombre='Luis', apellido='López',
            email='luis@example.com', telefono='0981 100 002', cargo='Auxiliar',
        )
        direccion = Direccion.objects.create(
            contacto=contacto, direccion='Calle Temporal', codigo_postal='1000',
            tipo=Direccion.Tipo.OTRO, ciudad=self.ciudad,
        )

        self.client.post(reverse('empresas:empresa_eliminar', args=[empresa.pk]))

        self.assertFalse(Empresa.objects.filter(pk=empresa.pk).exists())
        self.assertFalse(Contacto.objects.filter(pk=contacto.pk).exists())
        self.assertFalse(Direccion.objects.filter(pk=direccion.pk).exists())

    def test_contacto_anidado_ignora_empresa_manipulada(self):
        otra_empresa = Empresa.objects.create(
            razon_social='Otra Empresa S.A.', ruc='80001003-0',
            email='otra@example.com', telefono='021 100 003', es_cliente=True,
        )
        respuesta = self.client.post(
            reverse('empresas:empresa_contacto_crear', args=[self.empresa.pk]),
            {'empresa': otra_empresa.pk, 'nombre': 'Carlos', 'apellido': 'Pérez',
             'email': 'carlos@example.com', 'telefono': '0981 100 003', 'cargo': 'Ventas'},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Contacto.objects.get(email='carlos@example.com').empresa, self.empresa)

    def test_direccion_anidada_ignora_contacto_manipulado(self):
        otro_contacto = Contacto.objects.create(
            empresa=self.empresa, nombre='Mario', apellido='Ruiz',
            email='mario@example.com', telefono='0981 100 004', cargo='Ventas',
        )
        respuesta = self.client.post(
            reverse('empresas:contacto_direccion_crear', args=[self.contacto.pk]),
            {'contacto': otro_contacto.pk, 'direccion': 'Calle Protegida 123',
             'codigo_postal': '1210', 'tipo': Direccion.Tipo.PARTICULAR,
             'ciudad': self.ciudad.pk},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Direccion.objects.get(direccion='Calle Protegida 123').contacto, self.contacto)

    def test_categoria_se_desasocia_sin_eliminar_empresa(self):
        self.empresa.categorias.add(self.categoria)

        self.client.post(reverse('empresas:categoria_eliminar', args=[self.categoria.pk]))

        self.assertFalse(Categoria.objects.filter(pk=self.categoria.pk).exists())
        self.assertTrue(Empresa.objects.filter(pk=self.empresa.pk).exists())

    def test_registro_inexistente_devuelve_404(self):
        respuesta = self.client.get(reverse('empresas:empresa_detalle', args=[999999]))
        self.assertEqual(respuesta.status_code, 404)

    def test_actualiza_solo_usuario_de_modificacion(self):
        creador = get_user_model().objects.create_user(username='creador_admin')
        empresa = Empresa.objects.create(
            razon_social='Empresa Auditada S.A.',
            ruc='80000101-0',
            email='auditada@example.com',
            telefono='021 555 101',
            es_proveedor=True,
            usuario_creacion=creador,
            usuario_modificacion=creador,
        )
        solicitud = RequestFactory().post(f'/admin/empresas/empresa/{empresa.pk}/change/')
        solicitud.user = self.usuario

        EmpresaAdmin(Empresa, admin.site).save_model(
            solicitud,
            empresa,
            form=None,
            change=True,
        )

        self.assertEqual(empresa.usuario_creacion, creador)
        self.assertEqual(empresa.usuario_modificacion, self.usuario)


class BusquedaEmpresasPruebas(TestCase):
    """Verifica la búsqueda combinada del listado de empresas."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='buscador', password='Clave-segura-2026'
        )
        cls.farmacia = Empresa.objects.create(
            razon_social='Farmacia Central S.A.', ruc='80002000-1',
            email='contacto@farmaciacentral.com', telefono='021 200 001',
            es_cliente=True,
        )
        cls.tecnologia = Empresa.objects.create(
            razon_social='Tecnología del Sur S.R.L.', ruc='80003000-2',
            email='ventas@tecnologiasur.com', telefono='021 300 002',
            es_proveedor=True,
        )

    def setUp(self):
        self.client.force_login(self.usuario)
        self.url = reverse('empresas:empresa_lista')

    def obtener_empresas(self, termino):
        """Devuelve los resultados publicados por la vista para un término."""
        respuesta = self.client.get(self.url, {'q': termino})
        return respuesta, list(respuesta.context['empresas'])

    def test_busqueda_por_razon_social(self):
        respuesta, empresas = self.obtener_empresas('FARMACIA CENTRAL')
        self.assertEqual(empresas, [self.farmacia])
        self.assertContains(respuesta, 'value="FARMACIA CENTRAL"')

    def test_busqueda_por_ruc(self):
        _, empresas = self.obtener_empresas('80003000-2')
        self.assertEqual(empresas, [self.tecnologia])

    def test_busqueda_por_email(self):
        _, empresas = self.obtener_empresas('CONTACTO@FARMACIACENTRAL.COM')
        self.assertEqual(empresas, [self.farmacia])

    def test_busqueda_parcial(self):
        _, empresas = self.obtener_empresas('sur')
        self.assertEqual(empresas, [self.tecnologia])

    def test_busqueda_sin_coincidencias(self):
        respuesta, empresas = self.obtener_empresas('empresa inexistente')
        self.assertEqual(empresas, [])
        self.assertContains(respuesta, 'No se encontraron empresas')
        self.assertContains(respuesta, 'Limpiar')

    def test_busqueda_vacia_muestra_todas_las_empresas(self):
        respuesta, empresas = self.obtener_empresas('   ')
        self.assertCountEqual(empresas, [self.farmacia, self.tecnologia])
        self.assertEqual(respuesta.context['termino_busqueda'], '')

    def test_busqueda_requiere_autenticacion(self):
        self.client.logout()
        respuesta = self.client.get(self.url, {'q': 'farmacia'})
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta.url)


class FiltroTipoEmpresaPruebas(TestCase):
    """Verifica el filtro comercial y su combinación con la búsqueda."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='filtro_empresas', password='Clave-segura-2026'
        )
        cls.solo_cliente = Empresa.objects.create(
            razon_social='Cliente Norte S.A.', ruc='80004000-1',
            email='cliente@norte.com', telefono='021 400 001',
            es_cliente=True,
        )
        cls.solo_proveedor = Empresa.objects.create(
            razon_social='Proveedor Sur S.A.', ruc='80005000-2',
            email='proveedor@sur.com', telefono='021 500 002',
            es_proveedor=True,
        )
        cls.ambos = Empresa.objects.create(
            razon_social='Comercial Mixta S.A.', ruc='80006000-3',
            email='contacto@mixta.com', telefono='021 600 003',
            es_cliente=True, es_proveedor=True,
        )

    def setUp(self):
        self.client.force_login(self.usuario)
        self.url = reverse('empresas:empresa_lista')

    def obtener_empresas(self, **parametros):
        """Consulta el listado y materializa sus resultados filtrados."""
        respuesta = self.client.get(self.url, parametros)
        return respuesta, list(respuesta.context['empresas'])

    def test_filtro_todos(self):
        respuesta, empresas = self.obtener_empresas(tipo='todos')

        self.assertCountEqual(
            empresas, [self.solo_cliente, self.solo_proveedor, self.ambos]
        )
        self.assertEqual(respuesta.context['tipo_empresa'], 'todos')

    def test_filtro_clientes_incluye_empresas_que_son_ambos(self):
        _, empresas = self.obtener_empresas(tipo='clientes')
        self.assertCountEqual(empresas, [self.solo_cliente, self.ambos])

    def test_filtro_proveedores_incluye_empresas_que_son_ambos(self):
        _, empresas = self.obtener_empresas(tipo='proveedores')
        self.assertCountEqual(empresas, [self.solo_proveedor, self.ambos])

    def test_filtro_ambos(self):
        respuesta, empresas = self.obtener_empresas(tipo='ambos')

        self.assertEqual(empresas, [self.ambos])
        self.assertContains(respuesta, 'value="ambos" selected')

    def test_empresa_ambos_cumple_cada_filtro_individual(self):
        for tipo in ('clientes', 'proveedores', 'ambos'):
            with self.subTest(tipo=tipo):
                _, empresas = self.obtener_empresas(tipo=tipo)
                self.assertIn(self.ambos, empresas)

    def test_combina_busqueda_con_filtro(self):
        respuesta, empresas = self.obtener_empresas(q='comercial', tipo='clientes')

        self.assertEqual(empresas, [self.ambos])
        self.assertEqual(respuesta.context['termino_busqueda'], 'comercial')
        self.assertEqual(respuesta.context['tipo_empresa'], 'clientes')

    def test_parametro_desconocido_utiliza_todos(self):
        respuesta, empresas = self.obtener_empresas(tipo='desconocido')

        self.assertCountEqual(
            empresas, [self.solo_cliente, self.solo_proveedor, self.ambos]
        )
        self.assertEqual(respuesta.context['tipo_empresa'], 'todos')

    def test_resultado_sin_coincidencias(self):
        respuesta, empresas = self.obtener_empresas(
            q='Cliente Norte', tipo='proveedores'
        )

        self.assertEqual(empresas, [])
        self.assertContains(respuesta, 'No se encontraron empresas')
        self.assertContains(respuesta, 'Limpiar')

    def test_filtro_requiere_autenticacion(self):
        self.client.logout()
        respuesta = self.client.get(self.url, {'tipo': 'clientes'})

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta.url)


class PaginacionEmpresasPruebas(TestCase):
    """Verifica límites, navegación y conservación de filtros."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='paginador', password='Clave-segura-2026'
        )
        cls.categoria = Categoria.objects.create(
            nombre='Categoría paginada', descripcion='Pruebas de paginación'
        )

    def setUp(self):
        self.client.force_login(self.usuario)
        self.url = reverse('empresas:empresa_lista')

    def crear_empresas(self, cantidad, prefijo='Empresa'):
        empresas = Empresa.objects.bulk_create([
            Empresa(
                razon_social=f'{prefijo} {indice:03d}',
                ruc=f'PAG-{indice:05d}',
                email=f'empresa{indice}@example.com',
                telefono=f'021 {indice:06d}',
                es_cliente=True,
            )
            for indice in range(cantidad)
        ])
        for empresa in empresas:
            empresa.categorias.add(self.categoria)
        return empresas

    def test_diez_empresas_no_muestran_controles(self):
        self.crear_empresas(10)

        respuesta = self.client.get(self.url)

        self.assertFalse(respuesta.context['is_paginated'])
        self.assertEqual(len(respuesta.context['empresas']), 10)
        self.assertNotContains(respuesta, 'Paginación de resultados')

    def test_mas_de_diez_empresas_muestran_primera_pagina(self):
        self.crear_empresas(25)

        respuesta = self.client.get(self.url)
        pagina = respuesta.context['page_obj']

        self.assertTrue(respuesta.context['is_paginated'])
        self.assertEqual(len(respuesta.context['empresas']), 10)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (1, 10))
        self.assertContains(respuesta, 'Mostrando 1&ndash;10 de 25 empresas')

    def test_pagina_intermedia_muestra_rango_correcto(self):
        self.crear_empresas(25)

        respuesta = self.client.get(self.url, {'page': 2})
        pagina = respuesta.context['page_obj']

        self.assertEqual(pagina.number, 2)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (11, 20))
        self.assertContains(respuesta, 'Mostrando 11&ndash;20 de 25 empresas')

    def test_ultima_pagina_muestra_solo_restantes(self):
        self.crear_empresas(25)

        respuesta = self.client.get(self.url, {'page': 3})
        pagina = respuesta.context['page_obj']

        self.assertEqual(len(respuesta.context['empresas']), 5)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (21, 25))

    def test_pagina_inexistente_devuelve_404(self):
        self.crear_empresas(11)
        self.assertEqual(self.client.get(self.url, {'page': 99}).status_code, 404)

    def test_pagina_invalida_devuelve_404(self):
        self.crear_empresas(11)
        self.assertEqual(
            self.client.get(self.url, {'page': 'invalida'}).status_code, 404
        )

    def test_paginas_no_repiten_empresas(self):
        self.crear_empresas(20)

        primera = self.client.get(self.url, {'page': 1})
        primera_ids = {empresa.pk for empresa in primera.context['empresas']}
        segunda = self.client.get(self.url, {'page': 2})
        segunda_ids = {empresa.pk for empresa in segunda.context['empresas']}

        self.assertEqual(len(primera_ids | segunda_ids), 20)
        self.assertTrue(primera_ids.isdisjoint(segunda_ids))

    def test_orden_es_estable_cuando_se_repite_razon_social(self):
        empresas = self.crear_empresas(12, prefijo='Misma razón')
        Empresa.objects.filter(pk__in=[empresa.pk for empresa in empresas]).update(
            razon_social='Misma razón'
        )

        primera = self.client.get(self.url, {'page': 1})
        segunda = self.client.get(self.url, {'page': 2})
        ids = [empresa.pk for empresa in primera.context['empresas']]
        ids += [empresa.pk for empresa in segunda.context['empresas']]

        self.assertEqual(ids, sorted(ids))

    def test_conserva_busqueda_y_filtro_comercial_en_enlaces(self):
        self.crear_empresas(15, prefijo='Comercial')

        respuesta = self.client.get(
            self.url, {'q': 'Comercial', 'tipo': 'clientes'}
        )

        self.assertEqual(
            respuesta.context['parametros_paginacion'],
            'q=Comercial&tipo=clientes',
        )
        self.assertContains(
            respuesta, '?q=Comercial&amp;tipo=clientes&amp;page=2'
        )

    def test_conserva_categoria_y_descarta_pagina_anterior(self):
        self.crear_empresas(15)

        respuesta = self.client.get(
            self.url, {'categoria': self.categoria.pk, 'page': 2}
        )

        self.assertEqual(
            respuesta.context['parametros_paginacion'],
            f'categoria={self.categoria.pk}',
        )
        self.assertNotIn('page=', respuesta.context['parametros_paginacion'])

    def test_paginacion_requiere_autenticacion(self):
        self.crear_empresas(11)
        self.client.logout()

        respuesta = self.client.get(self.url, {'page': 2})

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta.url)


class PaginacionContactosPruebas(TestCase):
    """Verifica la paginación nativa del listado general de contactos."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='paginador_contactos', password='Clave-segura-2026'
        )
        cls.empresa = Empresa.objects.create(
            razon_social='Empresa de contactos S.A.',
            ruc='PAG-CONTACTOS-1',
            email='contactos@example.com',
            telefono='021 700 000',
            es_cliente=True,
        )

    def setUp(self):
        self.client.force_login(self.usuario)
        self.url = reverse('empresas:contacto_lista')

    def crear_contactos(self, cantidad, apellido='Apellido'):
        return Contacto.objects.bulk_create([
            Contacto(
                empresa=self.empresa,
                nombre=f'Nombre {indice:03d}',
                apellido=apellido,
                email=f'contacto{indice}@example.com',
                telefono=f'0981 {indice:06d}',
                cargo='Contacto de prueba',
            )
            for indice in range(cantidad)
        ])

    def test_menos_de_diez_contactos_no_muestran_controles(self):
        self.crear_contactos(9)

        respuesta = self.client.get(self.url)

        self.assertFalse(respuesta.context['is_paginated'])
        self.assertEqual(len(respuesta.context['contactos']), 9)
        self.assertNotContains(respuesta, 'Paginación de resultados')

    def test_diez_contactos_no_muestran_controles(self):
        self.crear_contactos(10)

        respuesta = self.client.get(self.url)

        self.assertFalse(respuesta.context['is_paginated'])
        self.assertEqual(len(respuesta.context['contactos']), 10)

    def test_mas_de_diez_contactos_activan_paginacion(self):
        self.crear_contactos(11)

        respuesta = self.client.get(self.url)

        self.assertTrue(respuesta.context['is_paginated'])
        self.assertContains(respuesta, 'Paginación de resultados')

    def test_primera_pagina_muestra_diez_contactos(self):
        self.crear_contactos(25)

        respuesta = self.client.get(self.url)
        pagina = respuesta.context['page_obj']

        self.assertEqual(len(respuesta.context['contactos']), 10)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (1, 10))
        self.assertContains(respuesta, 'Mostrando 1&ndash;10 de 25 contactos')

    def test_pagina_intermedia_muestra_rango_correcto(self):
        self.crear_contactos(25)

        respuesta = self.client.get(self.url, {'page': 2})
        pagina = respuesta.context['page_obj']

        self.assertEqual(pagina.number, 2)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (11, 20))
        self.assertContains(respuesta, 'Mostrando 11&ndash;20 de 25 contactos')

    def test_ultima_pagina_muestra_contactos_restantes(self):
        self.crear_contactos(25)

        respuesta = self.client.get(self.url, {'page': 3})
        pagina = respuesta.context['page_obj']

        self.assertEqual(len(respuesta.context['contactos']), 5)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (21, 25))

    def test_pagina_inexistente_devuelve_404(self):
        self.crear_contactos(11)
        self.assertEqual(self.client.get(self.url, {'page': 99}).status_code, 404)

    def test_pagina_invalida_devuelve_404(self):
        self.crear_contactos(11)
        self.assertEqual(
            self.client.get(self.url, {'page': 'invalida'}).status_code, 404
        )

    def test_orden_es_estable_por_apellido_nombre_e_identificador(self):
        contactos = self.crear_contactos(12, apellido='Mismo apellido')
        Contacto.objects.filter(
            pk__in=[contacto.pk for contacto in contactos]
        ).update(nombre='Mismo nombre')

        primera = self.client.get(self.url, {'page': 1})
        segunda = self.client.get(self.url, {'page': 2})
        ids = [contacto.pk for contacto in primera.context['contactos']]
        ids += [contacto.pk for contacto in segunda.context['contactos']]

        self.assertEqual(ids, sorted(ids))

    def test_conserva_parametro_get_de_empresa(self):
        self.crear_contactos(11)

        respuesta = self.client.get(self.url, {'empresa': self.empresa.pk})

        self.assertEqual(
            respuesta.context['parametros_paginacion'],
            f'empresa={self.empresa.pk}',
        )
        self.assertContains(
            respuesta, f'?empresa={self.empresa.pk}&amp;page=2'
        )

    def test_paginas_no_repiten_contactos(self):
        self.crear_contactos(20)

        primera = self.client.get(self.url, {'page': 1})
        primera_ids = {contacto.pk for contacto in primera.context['contactos']}
        segunda = self.client.get(self.url, {'page': 2})
        segunda_ids = {contacto.pk for contacto in segunda.context['contactos']}

        self.assertEqual(len(primera_ids | segunda_ids), 20)
        self.assertTrue(primera_ids.isdisjoint(segunda_ids))

    def test_paginacion_requiere_autenticacion(self):
        self.crear_contactos(11)
        self.client.logout()

        respuesta = self.client.get(self.url, {'page': 2})

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta.url)


class PaginacionDireccionesPruebas(TestCase):
    """Verifica la paginación nativa del listado general de direcciones."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='paginador_direcciones', password='Clave-segura-2026'
        )
        cls.departamento = Departamento.objects.create(nombre='Itapúa')
        cls.ciudad = Ciudad.objects.create(
            nombre='Encarnación', departamento=cls.departamento
        )
        cls.empresa = Empresa.objects.create(
            razon_social='Empresa de direcciones S.A.',
            ruc='PAG-DIRECCIONES-1',
            email='direcciones@example.com',
            telefono='071 700 000',
            es_cliente=True,
        )
        cls.contacto = Contacto.objects.create(
            empresa=cls.empresa,
            nombre='Contacto',
            apellido='Direcciones',
            email='contacto.direcciones@example.com',
            telefono='0985 700 000',
            cargo='Encargado',
        )

    def setUp(self):
        self.client.force_login(self.usuario)
        self.url = reverse('empresas:direccion_lista')

    def crear_direcciones(self, cantidad):
        return Direccion.objects.bulk_create([
            Direccion(
                contacto=self.contacto,
                direccion=f'Calle de prueba {indice:03d}',
                codigo_postal=f'{indice:04d}',
                tipo=Direccion.Tipo.LABORAL,
                ciudad=self.ciudad,
            )
            for indice in range(cantidad)
        ])

    def test_menos_de_diez_direcciones_no_muestran_controles(self):
        self.crear_direcciones(9)

        respuesta = self.client.get(self.url)

        self.assertFalse(respuesta.context['is_paginated'])
        self.assertEqual(len(respuesta.context['direcciones']), 9)
        self.assertNotContains(respuesta, 'Paginación de resultados')

    def test_diez_direcciones_no_muestran_controles(self):
        self.crear_direcciones(10)

        respuesta = self.client.get(self.url)

        self.assertFalse(respuesta.context['is_paginated'])
        self.assertEqual(len(respuesta.context['direcciones']), 10)

    def test_mas_de_diez_direcciones_activan_paginacion(self):
        self.crear_direcciones(11)

        respuesta = self.client.get(self.url)

        self.assertTrue(respuesta.context['is_paginated'])
        self.assertContains(respuesta, 'Paginación de resultados')

    def test_primera_pagina_muestra_diez_direcciones(self):
        self.crear_direcciones(25)

        respuesta = self.client.get(self.url)
        pagina = respuesta.context['page_obj']

        self.assertEqual(len(respuesta.context['direcciones']), 10)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (1, 10))
        self.assertContains(respuesta, 'Mostrando 1&ndash;10 de 25 direcciones')

    def test_pagina_intermedia_muestra_rango_correcto(self):
        self.crear_direcciones(25)

        respuesta = self.client.get(self.url, {'page': 2})
        pagina = respuesta.context['page_obj']

        self.assertEqual(pagina.number, 2)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (11, 20))
        self.assertContains(
            respuesta, 'Mostrando 11&ndash;20 de 25 direcciones'
        )

    def test_ultima_pagina_muestra_direcciones_restantes(self):
        self.crear_direcciones(25)

        respuesta = self.client.get(self.url, {'page': 3})
        pagina = respuesta.context['page_obj']

        self.assertEqual(len(respuesta.context['direcciones']), 5)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (21, 25))

    def test_pagina_inexistente_devuelve_404(self):
        self.crear_direcciones(11)
        self.assertEqual(self.client.get(self.url, {'page': 99}).status_code, 404)

    def test_pagina_invalida_devuelve_404(self):
        self.crear_direcciones(11)
        self.assertEqual(
            self.client.get(self.url, {'page': 'invalida'}).status_code, 404
        )

    def test_orden_es_estable_por_identificador(self):
        direcciones = self.crear_direcciones(12)

        primera = self.client.get(self.url, {'page': 1})
        segunda = self.client.get(self.url, {'page': 2})
        ids = [direccion.pk for direccion in primera.context['direcciones']]
        ids += [direccion.pk for direccion in segunda.context['direcciones']]

        self.assertEqual(ids, [direccion.pk for direccion in direcciones])

    def test_conserva_parametros_get_vigentes(self):
        self.crear_direcciones(11)

        respuesta = self.client.get(
            self.url,
            {'contacto': self.contacto.pk, 'ciudad': self.ciudad.pk},
        )

        self.assertEqual(
            respuesta.context['parametros_paginacion'],
            f'contacto={self.contacto.pk}&ciudad={self.ciudad.pk}',
        )
        self.assertContains(
            respuesta,
            f'?contacto={self.contacto.pk}&amp;ciudad={self.ciudad.pk}&amp;page=2',
        )

    def test_paginas_no_repiten_direcciones(self):
        self.crear_direcciones(20)

        primera = self.client.get(self.url, {'page': 1})
        primera_ids = {
            direccion.pk for direccion in primera.context['direcciones']
        }
        segunda = self.client.get(self.url, {'page': 2})
        segunda_ids = {
            direccion.pk for direccion in segunda.context['direcciones']
        }

        self.assertEqual(len(primera_ids | segunda_ids), 20)
        self.assertTrue(primera_ids.isdisjoint(segunda_ids))

    def test_paginacion_requiere_autenticacion(self):
        self.crear_direcciones(11)
        self.client.logout()

        respuesta = self.client.get(self.url, {'page': 2})

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta.url)


class PaginacionCategoriasPruebas(TestCase):
    """Verifica la paginación y el orden del listado de categorías."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='paginador_categorias', password='Clave-segura-2026'
        )

    def setUp(self):
        self.client.force_login(self.usuario)
        self.url = reverse('empresas:categoria_lista')

    def crear_categorias(self, cantidad):
        return Categoria.objects.bulk_create([
            Categoria(
                nombre=f'Categoría {indice:03d}',
                descripcion=f'Descripción de categoría {indice:03d}',
            )
            for indice in range(cantidad)
        ])

    def test_menos_de_diez_categorias_no_muestran_controles(self):
        self.crear_categorias(9)

        respuesta = self.client.get(self.url)

        self.assertFalse(respuesta.context['is_paginated'])
        self.assertEqual(len(respuesta.context['categorias']), 9)
        self.assertNotContains(respuesta, 'Paginación de resultados')

    def test_diez_categorias_no_muestran_controles(self):
        self.crear_categorias(10)

        respuesta = self.client.get(self.url)

        self.assertFalse(respuesta.context['is_paginated'])
        self.assertEqual(len(respuesta.context['categorias']), 10)

    def test_mas_de_diez_categorias_activan_paginacion(self):
        self.crear_categorias(11)

        respuesta = self.client.get(self.url)

        self.assertTrue(respuesta.context['is_paginated'])
        self.assertContains(respuesta, 'Paginación de resultados')

    def test_primera_pagina_muestra_diez_categorias(self):
        self.crear_categorias(25)

        respuesta = self.client.get(self.url)
        pagina = respuesta.context['page_obj']

        self.assertEqual(len(respuesta.context['categorias']), 10)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (1, 10))
        self.assertContains(respuesta, 'Mostrando 1&ndash;10 de 25 categorías')

    def test_pagina_intermedia_muestra_rango_correcto(self):
        self.crear_categorias(25)

        respuesta = self.client.get(self.url, {'page': 2})
        pagina = respuesta.context['page_obj']

        self.assertEqual(pagina.number, 2)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (11, 20))
        self.assertContains(
            respuesta, 'Mostrando 11&ndash;20 de 25 categorías'
        )

    def test_ultima_pagina_muestra_categorias_restantes(self):
        self.crear_categorias(25)

        respuesta = self.client.get(self.url, {'page': 3})
        pagina = respuesta.context['page_obj']

        self.assertEqual(len(respuesta.context['categorias']), 5)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (21, 25))

    def test_pagina_inexistente_devuelve_404(self):
        self.crear_categorias(11)
        self.assertEqual(self.client.get(self.url, {'page': 99}).status_code, 404)

    def test_pagina_invalida_devuelve_404(self):
        self.crear_categorias(11)
        self.assertEqual(
            self.client.get(self.url, {'page': 'invalida'}).status_code, 404
        )

    def test_orden_alfabetico_se_conserva_entre_paginas(self):
        nombres = [
            'Zulu', 'Alfa', 'Hotel', 'Bravo', 'India', 'Charlie',
            'Juliet', 'Delta', 'Kilo', 'Echo', 'Lima', 'Foxtrot',
        ]
        Categoria.objects.bulk_create([
            Categoria(nombre=nombre, descripcion='Orden alfabético')
            for nombre in nombres
        ])

        primera = self.client.get(self.url, {'page': 1})
        segunda = self.client.get(self.url, {'page': 2})
        obtenidos = [
            categoria.nombre for categoria in primera.context['categorias']
        ]
        obtenidos += [
            categoria.nombre for categoria in segunda.context['categorias']
        ]

        self.assertEqual(obtenidos, sorted(nombres))

    def test_conserva_parametros_get_vigentes(self):
        self.crear_categorias(11)

        respuesta = self.client.get(self.url, {'estado': 'activo'})

        self.assertEqual(
            respuesta.context['parametros_paginacion'], 'estado=activo'
        )
        self.assertContains(respuesta, '?estado=activo&amp;page=2')

    def test_paginas_no_repiten_categorias(self):
        self.crear_categorias(20)

        primera = self.client.get(self.url, {'page': 1})
        primera_ids = {
            categoria.pk for categoria in primera.context['categorias']
        }
        segunda = self.client.get(self.url, {'page': 2})
        segunda_ids = {
            categoria.pk for categoria in segunda.context['categorias']
        }

        self.assertEqual(len(primera_ids | segunda_ids), 20)
        self.assertTrue(primera_ids.isdisjoint(segunda_ids))

    def test_paginacion_requiere_autenticacion(self):
        self.crear_categorias(11)
        self.client.logout()

        respuesta = self.client.get(self.url, {'page': 2})

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta.url)
