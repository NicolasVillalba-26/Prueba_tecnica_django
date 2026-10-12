from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from empresas.admin import EmpresaAdmin
from empresas.forms import EmpresaFormulario
from empresas.models import Empresa


class AuditoriaEmpresaPruebas(TestCase):
    """Verifica la trazabilidad automática y la protección de sus campos."""

    @classmethod
    def setUpTestData(cls):
        cls.creador = get_user_model().objects.create_user(
            username='creador_auditoria', password='Clave-segura-2026'
        )
        cls.editor = get_user_model().objects.create_user(
            username='editor_auditoria', password='Clave-segura-2026'
        )
        cls.administrador = get_user_model().objects.create_superuser(
            username='admin_auditoria',
            email='admin.auditoria@example.com',
            password='Clave-segura-2026',
        )

    def datos_empresa(self, **cambios):
        """Genera datos válidos para los formularios de empresa."""
        datos = {
            'razon_social': 'Empresa auditada S.A.',
            'ruc': '80300001-1',
            'email': 'auditada@example.com',
            'telefono': '021 300 001',
            'es_cliente': 'on',
            'activo': 'on',
        }
        datos.update(cambios)
        return datos

    def crear_desde_vista(self, **cambios):
        """Crea una empresa mediante el flujo web autenticado."""
        self.client.force_login(self.creador)
        respuesta = self.client.post(
            reverse('empresas:empresa_crear'),
            self.datos_empresa(**cambios),
        )
        empresa = Empresa.objects.get(ruc=cambios.get('ruc', '80300001-1'))
        return respuesta, empresa

    def test_creacion_asigna_ambos_usuarios_y_fechas(self):
        respuesta, empresa = self.crear_desde_vista()

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(empresa.usuario_creacion, self.creador)
        self.assertEqual(empresa.usuario_modificacion, self.creador)
        self.assertIsNotNone(empresa.fecha_creacion)
        self.assertIsNotNone(empresa.fecha_modificacion)

    def test_modificacion_por_otro_usuario_actualiza_solo_modificador(self):
        _, empresa = self.crear_desde_vista()
        fecha_creacion = empresa.fecha_creacion
        fecha_modificacion = empresa.fecha_modificacion
        self.client.force_login(self.editor)

        respuesta = self.client.post(
            reverse('empresas:empresa_editar', args=[empresa.pk]),
            self.datos_empresa(razon_social='Empresa editada S.A.'),
        )
        empresa.refresh_from_db()

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(empresa.usuario_creacion, self.creador)
        self.assertEqual(empresa.usuario_modificacion, self.editor)
        self.assertEqual(empresa.fecha_creacion, fecha_creacion)
        self.assertGreater(empresa.fecha_modificacion, fecha_modificacion)

    def test_post_no_puede_falsificar_usuarios_de_auditoria(self):
        self.client.force_login(self.creador)

        self.client.post(
            reverse('empresas:empresa_crear'),
            self.datos_empresa(
                usuario_creacion=self.editor.pk,
                usuario_modificacion=self.editor.pk,
            ),
        )
        empresa = Empresa.objects.get(ruc='80300001-1')

        self.assertEqual(empresa.usuario_creacion, self.creador)
        self.assertEqual(empresa.usuario_modificacion, self.creador)

    def test_edicion_no_puede_cambiar_creador_mediante_post(self):
        _, empresa = self.crear_desde_vista()
        self.client.force_login(self.editor)

        self.client.post(
            reverse('empresas:empresa_editar', args=[empresa.pk]),
            self.datos_empresa(usuario_creacion=self.editor.pk),
        )
        empresa.refresh_from_db()

        self.assertEqual(empresa.usuario_creacion, self.creador)
        self.assertEqual(empresa.usuario_modificacion, self.editor)

    def test_formulario_excluye_todos_los_campos_de_auditoria(self):
        formulario = EmpresaFormulario()

        for campo in (
            'fecha_creacion',
            'fecha_modificacion',
            'usuario_creacion',
            'usuario_modificacion',
        ):
            with self.subTest(campo=campo):
                self.assertNotIn(campo, formulario.fields)

    def test_admin_marca_campos_de_auditoria_como_solo_lectura(self):
        administrador_modelo = EmpresaAdmin(Empresa, admin.site)

        for campo in (
            'fecha_creacion',
            'fecha_modificacion',
            'usuario_creacion',
            'usuario_modificacion',
        ):
            with self.subTest(campo=campo):
                self.assertIn(campo, administrador_modelo.readonly_fields)

    def test_admin_asigna_auditoria_al_crear(self):
        empresa = Empresa(
            razon_social='Empresa desde Admin S.A.',
            ruc='80300002-2',
            email='admin.creacion@example.com',
            telefono='021 300 002',
            es_cliente=True,
        )
        solicitud = RequestFactory().post('/admin/empresas/empresa/add/')
        solicitud.user = self.administrador

        EmpresaAdmin(Empresa, admin.site).save_model(
            solicitud, empresa, form=None, change=False
        )

        self.assertEqual(empresa.usuario_creacion, self.administrador)
        self.assertEqual(empresa.usuario_modificacion, self.administrador)
        self.assertIsNotNone(empresa.fecha_creacion)
        self.assertIsNotNone(empresa.fecha_modificacion)

    def test_admin_conserva_creador_y_actualiza_modificador(self):
        empresa = Empresa.objects.create(
            razon_social='Empresa Admin editable S.A.',
            ruc='80300003-3',
            email='admin.edicion@example.com',
            telefono='021 300 003',
            es_proveedor=True,
            usuario_creacion=self.creador,
            usuario_modificacion=self.creador,
        )
        fecha_creacion = empresa.fecha_creacion
        solicitud = RequestFactory().post(
            f'/admin/empresas/empresa/{empresa.pk}/change/'
        )
        solicitud.user = self.administrador

        EmpresaAdmin(Empresa, admin.site).save_model(
            solicitud, empresa, form=None, change=True
        )
        empresa.refresh_from_db()

        self.assertEqual(empresa.usuario_creacion, self.creador)
        self.assertEqual(empresa.usuario_modificacion, self.administrador)
        self.assertEqual(empresa.fecha_creacion, fecha_creacion)

    def test_detalle_muestra_datos_de_auditoria(self):
        _, empresa = self.crear_desde_vista()

        respuesta = self.client.get(
            reverse('empresas:empresa_detalle', args=[empresa.pk])
        )

        self.assertContains(respuesta, 'Auditoría')
        self.assertContains(respuesta, self.creador.username)
        self.assertContains(respuesta, 'Creación')
        self.assertContains(respuesta, 'Última modificación')

    def test_eliminar_usuario_conserva_empresa_con_auditoria_nula(self):
        _, empresa = self.crear_desde_vista()

        self.creador.delete()
        empresa.refresh_from_db()

        self.assertTrue(Empresa.objects.filter(pk=empresa.pk).exists())
        self.assertIsNone(empresa.usuario_creacion)
        self.assertIsNone(empresa.usuario_modificacion)
