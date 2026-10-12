from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from ubicaciones.models import Ciudad, Departamento


class CrudUbicacionesPruebas(TestCase):
    """Verifica altas, cambios, bajas y restricciones desde la interfaz."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='operador_ubicaciones', password='Clave-segura-2026'
        )
        cls.departamento = Departamento.objects.create(nombre='Central')
        cls.ciudad = Ciudad.objects.create(
            nombre='San Lorenzo', departamento=cls.departamento
        )

    def setUp(self):
        self.usuario.user_permissions.set(Permission.objects.all())
        self.client.force_login(self.usuario)

    def test_rutas_requieren_autenticacion(self):
        self.client.logout()
        for nombre in ('departamento_lista', 'ciudad_lista'):
            with self.subTest(nombre=nombre):
                respuesta = self.client.get(reverse(f'ubicaciones:{nombre}'))
                self.assertEqual(respuesta.status_code, 302)
                self.assertIn(reverse('login'), respuesta.url)

    def test_crear_y_editar_departamento(self):
        respuesta = self.client.post(
            reverse('ubicaciones:departamento_crear'), {'nombre': 'Cordillera'}
        )
        departamento = Departamento.objects.get(nombre='Cordillera')
        self.assertRedirects(respuesta, reverse('ubicaciones:departamento_lista'))

        self.client.post(
            reverse('ubicaciones:departamento_editar', args=[departamento.pk]),
            {'nombre': 'Cordillera actualizada'},
        )
        departamento.refresh_from_db()
        self.assertEqual(departamento.nombre, 'Cordillera actualizada')

    def test_rechaza_departamento_duplicado(self):
        respuesta = self.client.post(
            reverse('ubicaciones:departamento_crear'), {'nombre': 'Central'}
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Ya existe')
        self.assertEqual(Departamento.objects.filter(nombre='Central').count(), 1)

    def test_crear_y_editar_ciudad(self):
        respuesta = self.client.post(
            reverse('ubicaciones:ciudad_crear'),
            {'nombre': 'Luque', 'departamento': self.departamento.pk},
        )
        ciudad = Ciudad.objects.get(nombre='Luque')
        self.assertRedirects(respuesta, reverse('ubicaciones:ciudad_lista'))

        self.client.post(
            reverse('ubicaciones:ciudad_editar', args=[ciudad.pk]),
            {'nombre': 'Luque Nueva', 'departamento': self.departamento.pk},
        )
        ciudad.refresh_from_db()
        self.assertEqual(ciudad.nombre, 'Luque Nueva')

    def test_rechaza_ciudad_duplicada_en_departamento(self):
        respuesta = self.client.post(
            reverse('ubicaciones:ciudad_crear'),
            {'nombre': self.ciudad.nombre, 'departamento': self.departamento.pk},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'ya existe')
        self.assertEqual(Ciudad.objects.filter(nombre='San Lorenzo').count(), 1)

    def test_no_elimina_departamento_con_ciudades(self):
        respuesta = self.client.post(
            reverse('ubicaciones:departamento_eliminar', args=[self.departamento.pk]),
            follow=True,
        )

        self.assertTrue(Departamento.objects.filter(pk=self.departamento.pk).exists())
        self.assertContains(respuesta, 'tiene ciudades asociadas')

    def test_get_solo_muestra_confirmacion_sin_eliminar(self):
        respuesta = self.client.get(
            reverse('ubicaciones:ciudad_eliminar', args=[self.ciudad.pk])
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(Ciudad.objects.filter(pk=self.ciudad.pk).exists())

    def test_elimina_ciudad_mediante_post(self):
        ciudad = Ciudad.objects.create(
            nombre='Villa Elisa', departamento=self.departamento
        )

        respuesta = self.client.post(
            reverse('ubicaciones:ciudad_eliminar', args=[ciudad.pk])
        )

        self.assertRedirects(respuesta, reverse('ubicaciones:ciudad_lista'))
        self.assertFalse(Ciudad.objects.filter(pk=ciudad.pk).exists())

    def test_registro_inexistente_devuelve_404(self):
        respuesta = self.client.get(
            reverse('ubicaciones:departamento_editar', args=[999999])
        )
        self.assertEqual(respuesta.status_code, 404)


class PaginacionCiudadesPruebas(TestCase):
    """Verifica la paginación y las relaciones del listado de ciudades."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='paginador_ciudades', password='Clave-segura-2026'
        )
        cls.departamento = Departamento.objects.create(nombre='Departamento A')

    def setUp(self):
        self.usuario.user_permissions.set(Permission.objects.all())
        self.client.force_login(self.usuario)
        self.url = reverse('ubicaciones:ciudad_lista')

    def crear_ciudades(self, cantidad):
        return Ciudad.objects.bulk_create([
            Ciudad(
                nombre=f'Ciudad {indice:03d}',
                departamento=self.departamento,
            )
            for indice in range(cantidad)
        ])

    def test_menos_de_diez_ciudades_no_muestran_controles(self):
        self.crear_ciudades(9)

        respuesta = self.client.get(self.url)

        self.assertFalse(respuesta.context['is_paginated'])
        self.assertEqual(len(respuesta.context['ciudades']), 9)
        self.assertNotContains(respuesta, 'Paginación de resultados')

    def test_diez_ciudades_no_muestran_controles(self):
        self.crear_ciudades(10)

        respuesta = self.client.get(self.url)

        self.assertFalse(respuesta.context['is_paginated'])
        self.assertEqual(len(respuesta.context['ciudades']), 10)

    def test_mas_de_diez_ciudades_activan_paginacion(self):
        self.crear_ciudades(11)

        respuesta = self.client.get(self.url)

        self.assertTrue(respuesta.context['is_paginated'])
        self.assertContains(respuesta, 'Paginación de resultados')

    def test_primera_pagina_muestra_diez_ciudades(self):
        self.crear_ciudades(25)

        respuesta = self.client.get(self.url)
        pagina = respuesta.context['page_obj']

        self.assertEqual(len(respuesta.context['ciudades']), 10)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (1, 10))
        self.assertContains(respuesta, 'Mostrando 1&ndash;10 de 25 ciudades')

    def test_pagina_intermedia_muestra_rango_correcto(self):
        self.crear_ciudades(25)

        respuesta = self.client.get(self.url, {'page': 2})
        pagina = respuesta.context['page_obj']

        self.assertEqual(pagina.number, 2)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (11, 20))
        self.assertContains(respuesta, 'Mostrando 11&ndash;20 de 25 ciudades')

    def test_ultima_pagina_muestra_ciudades_restantes(self):
        self.crear_ciudades(25)

        respuesta = self.client.get(self.url, {'page': 3})
        pagina = respuesta.context['page_obj']

        self.assertEqual(len(respuesta.context['ciudades']), 5)
        self.assertEqual((pagina.start_index(), pagina.end_index()), (21, 25))

    def test_pagina_inexistente_devuelve_404(self):
        self.crear_ciudades(11)
        self.assertEqual(self.client.get(self.url, {'page': 99}).status_code, 404)

    def test_pagina_invalida_devuelve_404(self):
        self.crear_ciudades(11)
        self.assertEqual(
            self.client.get(self.url, {'page': 'invalida'}).status_code, 404
        )

    def test_orden_alfabetico_se_conserva_entre_paginas(self):
        nombres = [
            'Zulu', 'Alfa', 'Hotel', 'Bravo', 'India', 'Charlie',
            'Juliet', 'Delta', 'Kilo', 'Echo', 'Lima', 'Foxtrot',
        ]
        Ciudad.objects.bulk_create([
            Ciudad(nombre=nombre, departamento=self.departamento)
            for nombre in nombres
        ])

        primera = self.client.get(self.url, {'page': 1})
        segunda = self.client.get(self.url, {'page': 2})
        obtenidos = [ciudad.nombre for ciudad in primera.context['ciudades']]
        obtenidos += [ciudad.nombre for ciudad in segunda.context['ciudades']]

        self.assertEqual(obtenidos, sorted(nombres))

    def test_muestra_departamento_asociado(self):
        Ciudad.objects.create(nombre='Ciudad relacionada', departamento=self.departamento)

        respuesta = self.client.get(self.url)

        self.assertContains(respuesta, self.departamento.nombre)
        self.assertEqual(
            respuesta.context['ciudades'][0].departamento,
            self.departamento,
        )

    def test_conserva_parametros_get_vigentes(self):
        self.crear_ciudades(11)

        respuesta = self.client.get(
            self.url, {'departamento': self.departamento.pk}
        )

        self.assertEqual(
            respuesta.context['parametros_paginacion'],
            f'departamento={self.departamento.pk}',
        )
        self.assertContains(
            respuesta, f'?departamento={self.departamento.pk}&amp;page=2'
        )

    def test_paginas_no_repiten_ciudades(self):
        self.crear_ciudades(20)

        primera = self.client.get(self.url, {'page': 1})
        primera_ids = {ciudad.pk for ciudad in primera.context['ciudades']}
        segunda = self.client.get(self.url, {'page': 2})
        segunda_ids = {ciudad.pk for ciudad in segunda.context['ciudades']}

        self.assertEqual(len(primera_ids | segunda_ids), 20)
        self.assertTrue(primera_ids.isdisjoint(segunda_ids))

    def test_paginacion_requiere_autenticacion(self):
        self.crear_ciudades(11)
        self.client.logout()

        respuesta = self.client.get(self.url, {'page': 2})

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta.url)
