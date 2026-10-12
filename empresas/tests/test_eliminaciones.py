from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db.models.deletion import RestrictedError
from django.test import TestCase
from django.urls import reverse

from empresas.models import Categoria, Contacto, Direccion, Empresa
from ubicaciones.models import Ciudad, Departamento


class EliminacionesRelacionadasPruebas(TestCase):
    """Comprueba eliminaciones permitidas, cascadas y relaciones protegidas."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='operador_eliminaciones', password='Clave-segura-2026'
        )

    def setUp(self):
        self.client.force_login(self.usuario)

    def crear_relaciones(self, sufijo='1'):
        """Crea una cadena empresa-contacto-dirección con ubicación propia."""
        departamento = Departamento.objects.create(nombre=f'Departamento {sufijo}')
        ciudad = Ciudad.objects.create(
            nombre=f'Ciudad {sufijo}', departamento=departamento
        )
        empresa = Empresa.objects.create(
            razon_social=f'Empresa {sufijo} S.A.',
            ruc=f'8020000{sufijo}-1',
            email=f'empresa{sufijo}@example.com',
            telefono='021 200 001',
            es_cliente=True,
        )
        contacto = Contacto.objects.create(
            empresa=empresa,
            nombre='Ana',
            apellido=f'Contacto {sufijo}',
            email=f'contacto{sufijo}@example.com',
            telefono='0981 200 001',
            cargo='Gerente',
        )
        direccion = Direccion.objects.create(
            contacto=contacto,
            direccion=f'Calle {sufijo}',
            codigo_postal='1000',
            tipo=Direccion.Tipo.LABORAL,
            ciudad=ciudad,
        )
        return departamento, ciudad, empresa, contacto, direccion

    def test_elimina_departamento_sin_ciudades(self):
        departamento = Departamento.objects.create(nombre='Sin ciudades')

        respuesta = self.client.post(
            reverse('ubicaciones:departamento_eliminar', args=[departamento.pk]),
            follow=True,
        )

        self.assertFalse(Departamento.objects.filter(pk=departamento.pk).exists())
        self.assertContains(respuesta, 'Departamento eliminado correctamente.')

    def test_bloquea_departamento_con_ciudades_y_conserva_registros(self):
        departamento, ciudad, _, _, _ = self.crear_relaciones('2')

        respuesta = self.client.post(
            reverse('ubicaciones:departamento_eliminar', args=[departamento.pk]),
            follow=True,
        )

        self.assertTrue(Departamento.objects.filter(pk=departamento.pk).exists())
        self.assertTrue(Ciudad.objects.filter(pk=ciudad.pk).exists())
        self.assertContains(
            respuesta,
            'No es posible eliminar el departamento porque tiene ciudades asociadas.',
        )

    def test_elimina_ciudad_sin_direcciones(self):
        departamento = Departamento.objects.create(nombre='Departamento libre')
        ciudad = Ciudad.objects.create(nombre='Ciudad libre', departamento=departamento)

        respuesta = self.client.post(
            reverse('ubicaciones:ciudad_eliminar', args=[ciudad.pk]), follow=True
        )

        self.assertFalse(Ciudad.objects.filter(pk=ciudad.pk).exists())
        self.assertContains(respuesta, 'Ciudad eliminada correctamente.')

    def test_bloquea_ciudad_con_direcciones_y_conserva_registros(self):
        _, ciudad, _, _, direccion = self.crear_relaciones('3')

        respuesta = self.client.post(
            reverse('ubicaciones:ciudad_eliminar', args=[ciudad.pk]), follow=True
        )

        self.assertTrue(Ciudad.objects.filter(pk=ciudad.pk).exists())
        self.assertTrue(Direccion.objects.filter(pk=direccion.pk).exists())
        self.assertContains(
            respuesta,
            'No es posible eliminar la ciudad porque está siendo utilizada en una o más direcciones.',
        )

    def test_confirmacion_protegida_advierte_y_oculta_boton(self):
        departamento, ciudad, _, _, _ = self.crear_relaciones('4')

        for ruta, objeto in (
            ('departamento_eliminar', departamento),
            ('ciudad_eliminar', ciudad),
        ):
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(
                    reverse(f'ubicaciones:{ruta}', args=[objeto.pk])
                )
                self.assertEqual(respuesta.status_code, 200)
                self.assertTrue(respuesta.context['eliminacion_bloqueada'])
                self.assertNotContains(respuesta, 'class="btn btn-danger"')

    def test_maneja_restricted_error_sin_responder_500(self):
        departamento = Departamento.objects.create(nombre='Restringido')
        error = RestrictedError('Eliminación restringida', {departamento})

        with patch.object(Departamento, 'delete', side_effect=error):
            respuesta = self.client.post(
                reverse(
                    'ubicaciones:departamento_eliminar', args=[departamento.pk]
                ),
                follow=True,
            )

        self.assertEqual(respuesta.status_code, 200)
        self.assertTrue(Departamento.objects.filter(pk=departamento.pk).exists())
        self.assertContains(respuesta, 'No es posible eliminar el departamento')

    def test_eliminar_empresa_aplica_cascade(self):
        _, _, empresa, contacto, direccion = self.crear_relaciones('5')

        self.client.post(reverse('empresas:empresa_eliminar', args=[empresa.pk]))

        self.assertFalse(Empresa.objects.filter(pk=empresa.pk).exists())
        self.assertFalse(Contacto.objects.filter(pk=contacto.pk).exists())
        self.assertFalse(Direccion.objects.filter(pk=direccion.pk).exists())

    def test_eliminar_contacto_aplica_cascade_sobre_direcciones(self):
        _, _, empresa, contacto, direccion = self.crear_relaciones('6')

        self.client.post(reverse('empresas:contacto_eliminar', args=[contacto.pk]))

        self.assertTrue(Empresa.objects.filter(pk=empresa.pk).exists())
        self.assertFalse(Contacto.objects.filter(pk=contacto.pk).exists())
        self.assertFalse(Direccion.objects.filter(pk=direccion.pk).exists())

    def test_eliminar_categoria_solo_quita_asociacion(self):
        _, _, empresa, _, _ = self.crear_relaciones('7')
        categoria = Categoria.objects.create(
            nombre='Categoría asociada', descripcion='Prueba'
        )
        empresa.categorias.add(categoria)

        self.client.post(
            reverse('empresas:categoria_eliminar', args=[categoria.pk])
        )

        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())
        self.assertTrue(Empresa.objects.filter(pk=empresa.pk).exists())

    def test_get_muestra_confirmacion_sin_eliminar(self):
        _, _, empresa, contacto, direccion = self.crear_relaciones('8')
        casos = (
            ('empresa_eliminar', empresa),
            ('contacto_eliminar', contacto),
            ('direccion_eliminar', direccion),
        )

        for ruta, objeto in casos:
            with self.subTest(ruta=ruta):
                respuesta = self.client.get(
                    reverse(f'empresas:{ruta}', args=[objeto.pk])
                )
                self.assertEqual(respuesta.status_code, 200)
                self.assertTrue(type(objeto).objects.filter(pk=objeto.pk).exists())

    def test_eliminacion_requiere_autenticacion(self):
        departamento = Departamento.objects.create(nombre='Protegido por sesión')
        self.client.logout()

        respuesta = self.client.post(
            reverse('ubicaciones:departamento_eliminar', args=[departamento.pk])
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta.url)
        self.assertTrue(Departamento.objects.filter(pk=departamento.pk).exists())
