from django.contrib.auth import get_user_model
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
