from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.urls import reverse

from empresas.models import Categoria, Contacto, Direccion, Empresa
from ubicaciones.models import Ciudad, Departamento


class PermisosCrudPruebas(TestCase):
    """Comprueba permisos nativos en backend, grupos y navegación."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='usuario_permisos', password='Clave-segura-2026'
        )
        cls.superusuario = get_user_model().objects.create_superuser(
            username='superusuario_permisos',
            email='superusuario@example.com',
            password='Clave-segura-2026',
        )
        cls.departamento = Departamento.objects.create(nombre='Central permisos')
        cls.ciudad = Ciudad.objects.create(
            nombre='Ciudad permisos', departamento=cls.departamento
        )
        cls.categoria = Categoria.objects.create(
            nombre='Categoría permisos', descripcion='Prueba de permisos'
        )
        cls.empresa = Empresa.objects.create(
            razon_social='Empresa permisos S.A.',
            ruc='80400001-1',
            email='permisos@example.com',
            telefono='021 400 001',
            es_cliente=True,
        )
        cls.contacto = Contacto.objects.create(
            empresa=cls.empresa,
            nombre='Ana',
            apellido='Permisos',
            email='ana.permisos@example.com',
            telefono='0981 400 001',
            cargo='Encargada',
        )
        cls.direccion = Direccion.objects.create(
            contacto=cls.contacto,
            direccion='Calle permisos 1',
            codigo_postal='1000',
            tipo=Direccion.Tipo.LABORAL,
            ciudad=cls.ciudad,
        )

    def setUp(self):
        self.client.force_login(self.usuario)

    def permiso(self, aplicacion, codigo):
        """Obtiene un permiso estándar por aplicación y nombre interno."""
        return Permission.objects.get(
            content_type__app_label=aplicacion,
            codename=codigo,
        )

    def asignar(self, *permisos):
        """Reemplaza permisos directos y renueva la sesión del usuario."""
        self.usuario.user_permissions.set(permisos)
        self.usuario = get_user_model().objects.get(pk=self.usuario.pk)
        self.client.force_login(self.usuario)

    def test_anonimo_es_redirigido_al_login(self):
        self.client.logout()

        respuesta = self.client.get(reverse('empresas:empresa_lista'))

        self.assertEqual(respuesta.status_code, 302)
        self.assertIn(reverse('login'), respuesta.url)

    def test_usuario_autenticado_sin_permiso_recibe_403_en_espanol(self):
        respuesta = self.client.get(reverse('empresas:empresa_lista'))

        self.assertEqual(respuesta.status_code, 403)
        self.assertContains(
            respuesta, 'No tiene permiso para realizar esta operación', status_code=403
        )

    def test_permiso_view_habilita_listados_de_cada_modelo(self):
        casos = (
            ('empresas', 'view_empresa', 'empresas:empresa_lista'),
            ('empresas', 'view_categoria', 'empresas:categoria_lista'),
            ('empresas', 'view_contacto', 'empresas:contacto_lista'),
            ('empresas', 'view_direccion', 'empresas:direccion_lista'),
            ('ubicaciones', 'view_ciudad', 'ubicaciones:ciudad_lista'),
            (
                'ubicaciones',
                'view_departamento',
                'ubicaciones:departamento_lista',
            ),
        )

        for aplicacion, codigo, ruta in casos:
            with self.subTest(codigo=codigo):
                self.asignar(self.permiso(aplicacion, codigo))
                self.assertEqual(self.client.get(reverse(ruta)).status_code, 200)

    def test_detalles_exigen_permiso_view_correspondiente(self):
        casos = (
            ('view_empresa', 'empresas:empresa_detalle', self.empresa.pk),
            ('view_contacto', 'empresas:contacto_detalle', self.contacto.pk),
        )

        for codigo, ruta, pk in casos:
            with self.subTest(codigo=codigo):
                self.asignar()
                self.assertEqual(self.client.get(reverse(ruta, args=[pk])).status_code, 403)
                self.asignar(self.permiso('empresas', codigo))
                self.assertEqual(self.client.get(reverse(ruta, args=[pk])).status_code, 200)

    def test_sin_permiso_add_no_puede_crear_por_post(self):
        respuesta = self.client.post(
            reverse('empresas:empresa_crear'),
            {
                'razon_social': 'Empresa bloqueada S.A.',
                'ruc': '80400002-2',
                'email': 'bloqueada@example.com',
                'telefono': '021 400 002',
                'es_cliente': 'on',
                'activo': 'on',
            },
        )

        self.assertEqual(respuesta.status_code, 403)
        self.assertFalse(Empresa.objects.filter(ruc='80400002-2').exists())

    def test_con_permiso_add_puede_crear_por_post(self):
        self.asignar(self.permiso('empresas', 'add_empresa'))

        respuesta = self.client.post(
            reverse('empresas:empresa_crear'),
            {
                'razon_social': 'Empresa autorizada S.A.',
                'ruc': '80400003-3',
                'email': 'autorizada@example.com',
                'telefono': '021 400 003',
                'es_cliente': 'on',
                'activo': 'on',
            },
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Empresa.objects.filter(ruc='80400003-3').exists())

    def test_change_protege_get_y_post(self):
        url = reverse('empresas:empresa_editar', args=[self.empresa.pk])
        datos = {
            'razon_social': 'Empresa modificada sin permiso',
            'ruc': self.empresa.ruc,
            'email': self.empresa.email,
            'telefono': self.empresa.telefono,
            'es_cliente': 'on',
            'activo': 'on',
        }

        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, datos).status_code, 403)
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.razon_social, 'Empresa permisos S.A.')

        self.asignar(self.permiso('empresas', 'change_empresa'))
        self.assertEqual(self.client.post(url, datos).status_code, 302)
        self.empresa.refresh_from_db()
        self.assertEqual(self.empresa.razon_social, datos['razon_social'])

    def test_delete_protege_get_y_post(self):
        empresa = Empresa.objects.create(
            razon_social='Empresa eliminable S.A.',
            ruc='80400004-4',
            email='eliminable@example.com',
            telefono='021 400 004',
            es_cliente=True,
        )
        url = reverse('empresas:empresa_eliminar', args=[empresa.pk])

        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertTrue(Empresa.objects.filter(pk=empresa.pk).exists())

        self.asignar(self.permiso('empresas', 'delete_empresa'))
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(Empresa.objects.filter(pk=empresa.pk).exists())

    def test_grupo_concede_permiso(self):
        grupo = Group.objects.create(name='Lectores de empresas')
        grupo.permissions.add(self.permiso('empresas', 'view_empresa'))
        self.usuario.groups.add(grupo)
        self.usuario = get_user_model().objects.get(pk=self.usuario.pk)
        self.client.force_login(self.usuario)

        respuesta = self.client.get(reverse('empresas:empresa_lista'))

        self.assertEqual(respuesta.status_code, 200)

    def test_superusuario_accede_a_todas_las_operaciones(self):
        self.client.force_login(self.superusuario)
        rutas = (
            reverse('empresas:empresa_lista'),
            reverse('empresas:empresa_crear'),
            reverse('empresas:empresa_editar', args=[self.empresa.pk]),
            reverse('empresas:empresa_eliminar', args=[self.empresa.pk]),
            reverse('ubicaciones:ciudad_lista'),
        )

        for ruta in rutas:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.client.get(ruta).status_code, 200)

    def test_botones_y_menu_respetan_permisos(self):
        self.asignar(self.permiso('empresas', 'view_empresa'))

        respuesta = self.client.get(reverse('empresas:empresa_lista'))

        self.assertContains(respuesta, 'Empresas')
        self.assertNotContains(respuesta, 'Nueva empresa')
        self.assertNotContains(respuesta, f'aria-label="Editar {self.empresa}"')
        self.assertNotContains(respuesta, f'aria-label="Eliminar {self.empresa}"')
        self.assertNotContains(respuesta, '>Contactos</p>')

        self.asignar(
            self.permiso('empresas', 'view_empresa'),
            self.permiso('empresas', 'add_empresa'),
            self.permiso('empresas', 'change_empresa'),
            self.permiso('empresas', 'delete_empresa'),
        )
        respuesta = self.client.get(reverse('empresas:empresa_lista'))
        self.assertContains(respuesta, 'Nueva empresa')
        self.assertContains(respuesta, f'aria-label="Editar {self.empresa}"')
        self.assertContains(respuesta, f'aria-label="Eliminar {self.empresa}"')

    def test_panel_principal_muestra_solo_accesos_permitidos(self):
        self.asignar(
            self.permiso('empresas', 'view_empresa'),
            self.permiso('ubicaciones', 'view_ciudad'),
        )

        respuesta = self.client.get(reverse('principal'))

        self.assertContains(respuesta, reverse('empresas:empresa_lista'))
        self.assertContains(respuesta, reverse('ubicaciones:ciudad_lista'))
        self.assertNotContains(respuesta, reverse('empresas:contacto_lista'))
        self.assertNotContains(
            respuesta, reverse('ubicaciones:departamento_lista')
        )
        self.assertNotContains(respuesta, 'Próximamente')

    def test_panel_oculta_modulos_si_no_hay_permisos_de_consulta(self):
        self.asignar()

        respuesta = self.client.get(reverse('principal'))

        self.assertNotContains(respuesta, 'Gestión comercial')
        self.assertNotContains(respuesta, '<h3 class="h5">Ubicaciones</h3>')
