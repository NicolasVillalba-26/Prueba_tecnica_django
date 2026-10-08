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
