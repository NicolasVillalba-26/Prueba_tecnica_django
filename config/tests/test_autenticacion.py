import re

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.staticfiles import finders
from django.test import Client, TestCase
from django.urls import reverse


class AutenticacionPruebas(TestCase):
    """Verifica el flujo completo de autenticación basada en sesiones."""

    @classmethod
    def setUpTestData(cls):
        cls.clave = 'Clave-segura-para-pruebas-2026'
        cls.usuario = get_user_model().objects.create_user(
            username='usuario_prueba',
            password=cls.clave,
        )

    def test_acceso_a_pagina_de_login(self):
        respuesta = self.client.get(reverse('login'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Iniciar sesión')
        self.assertContains(respuesta, 'csrfmiddlewaretoken')

    def test_inicio_de_sesion_con_credenciales_correctas(self):
        respuesta = self.client.post(
            reverse('login'),
            {'username': self.usuario.username, 'password': self.clave},
        )

        self.assertRedirects(respuesta, reverse('principal'))
        self.assertEqual(
            int(self.client.session['_auth_user_id']),
            self.usuario.pk,
        )

    def test_rechaza_credenciales_incorrectas_sin_revelar_usuario(self):
        respuesta = self.client.post(
            reverse('login'),
            {'username': self.usuario.username, 'password': 'incorrecta'},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, 'Usuario o contraseña incorrectos.')
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_usuario_anonimo_es_redirigido_al_login(self):
        respuesta = self.client.get(reverse('principal'))

        destino = f"{reverse('login')}?next={reverse('principal')}"
        self.assertRedirects(respuesta, destino)

    def test_usuario_autenticado_accede_a_pagina_principal(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.get(reverse('principal'))

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, self.usuario.username)
        self.assertContains(respuesta, 'Bienvenido al sistema')
        self.assertTemplateUsed(respuesta, 'base.html')
        self.assertTemplateUsed(respuesta, 'includes/navbar.html')
        self.assertTemplateUsed(respuesta, 'includes/sidebar.html')

    def test_recursos_principales_estan_disponibles(self):
        """Comprueba los recursos locales usados por la interfaz."""
        recursos = (
            'vendor/adminlte/css/adminlte.min.css',
            'vendor/adminlte/js/adminlte.min.js',
            'vendor/adminlte/js/bootstrap.bundle.min.js',
            'vendor/adminlte/icons/bootstrap-icons.min.css',
            'css/app.css',
            'js/app.js',
        )

        for recurso in recursos:
            with self.subTest(recurso=recurso):
                self.assertIsNotNone(finders.find(recurso))

    def test_sidebar_contiene_enlaces_a_crud(self):
        permisos_consulta = Permission.objects.filter(codename__startswith='view_')
        self.usuario.user_permissions.set(permisos_consulta)
        self.client.force_login(self.usuario)

        respuesta = self.client.get(reverse('principal'))

        self.assertContains(respuesta, 'Gestión comercial')
        self.assertContains(respuesta, reverse('empresas:empresa_lista'))
        self.assertContains(respuesta, reverse('empresas:contacto_lista'))
        self.assertContains(respuesta, reverse('empresas:direccion_lista'))
        self.assertContains(respuesta, reverse('empresas:categoria_lista'))
        self.assertContains(respuesta, reverse('ubicaciones:departamento_lista'))
        self.assertContains(respuesta, reverse('ubicaciones:ciudad_lista'))
        self.assertContains(respuesta, 'data-lte-toggle="sidebar"')

    def test_login_redirige_al_destino_original(self):
        destino = reverse('principal')
        respuesta = self.client.post(
            f"{reverse('login')}?next={destino}",
            {
                'username': self.usuario.username,
                'password': self.clave,
                'next': destino,
            },
        )

        self.assertRedirects(respuesta, destino)

    def test_logout_mediante_post_finaliza_sesion(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.post(reverse('logout'))

        self.assertRedirects(respuesta, reverse('login'))
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_mediante_get_no_esta_permitido(self):
        self.client.force_login(self.usuario)

        respuesta = self.client.get(reverse('logout'))

        self.assertEqual(respuesta.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_no_accede_a_pagina_protegida_despues_del_logout(self):
        self.client.force_login(self.usuario)
        self.client.post(reverse('logout'))

        respuesta = self.client.get(reverse('principal'))

        self.assertRedirects(
            respuesta,
            f"{reverse('login')}?next={reverse('principal')}",
        )

    def test_logout_requiere_token_csrf(self):
        cliente_csrf = Client(enforce_csrf_checks=True)
        cliente_csrf.force_login(self.usuario)

        respuesta_sin_token = cliente_csrf.post(reverse('logout'))
        self.assertEqual(respuesta_sin_token.status_code, 403)

        pagina_principal = cliente_csrf.get(reverse('principal'))
        coincidencia = re.search(
            r'name="csrfmiddlewaretoken" value="([^"]+)"',
            pagina_principal.content.decode(),
        )
        self.assertIsNotNone(coincidencia)

        respuesta_con_token = cliente_csrf.post(
            reverse('logout'),
            {'csrfmiddlewaretoken': coincidencia.group(1)},
        )
        self.assertRedirects(respuesta_con_token, reverse('login'))
