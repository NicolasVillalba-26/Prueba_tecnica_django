from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import RequestFactory, TestCase

from empresas.admin import EmpresaAdmin
from empresas.forms import EmpresaFormulario
from empresas.models import Empresa


class CondicionComercialPruebas(TestCase):
    """Comprueba la regla comercial en modelo, formularios, Admin y base."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_superuser(
            username='admin_condicion',
            email='admin.condicion@example.com',
            password='Clave-segura-2026',
        )
        cls.empresa = Empresa.objects.create(
            razon_social='Empresa comercial existente S.A.',
            ruc='80100001-1',
            email='comercial@example.com',
            telefono='021 100 001',
            es_cliente=True,
        )

    def crear_instancia(self, **cambios):
        """Construye una empresa no guardada con datos básicos válidos."""
        datos = {
            'razon_social': 'Empresa de condición S.A.',
            'ruc': '80100002-2',
            'email': 'condicion@example.com',
            'telefono': '021 100 002',
        }
        datos.update(cambios)
        return Empresa(**datos)

    def datos_formulario(self, **cambios):
        """Genera datos de formulario y permite variar las condiciones."""
        datos = {
            'razon_social': 'Empresa de formulario S.A.',
            'ruc': '80100003-3',
            'email': 'formulario@example.com',
            'telefono': '021 100 003',
            'activo': True,
        }
        datos.update(cambios)
        return datos

    def test_empresa_solo_cliente_es_valida(self):
        empresa = self.crear_instancia(es_cliente=True)
        empresa.full_clean()

    def test_empresa_solo_proveedora_es_valida(self):
        empresa = self.crear_instancia(es_proveedor=True)
        empresa.full_clean()

    def test_empresa_cliente_y_proveedora_es_valida(self):
        empresa = self.crear_instancia(es_cliente=True, es_proveedor=True)
        empresa.full_clean()

    def test_empresa_sin_condicion_es_invalida_mediante_full_clean(self):
        empresa = self.crear_instancia()

        with self.assertRaisesMessage(
            ValidationError,
            'La empresa debe ser cliente, proveedora o ambas.',
        ):
            empresa.full_clean()

    def test_formulario_crea_empresa_cliente(self):
        formulario = EmpresaFormulario(
            data=self.datos_formulario(es_cliente=True)
        )

        self.assertTrue(formulario.is_valid(), formulario.errors)
        empresa = formulario.save()
        self.assertTrue(empresa.es_cliente)
        self.assertFalse(empresa.es_proveedor)

    def test_formulario_edita_empresa_como_proveedora(self):
        formulario = EmpresaFormulario(
            data=self.datos_formulario(
                razon_social=self.empresa.razon_social,
                ruc=self.empresa.ruc,
                email=self.empresa.email,
                telefono=self.empresa.telefono,
                es_proveedor=True,
            ),
            instance=self.empresa,
        )

        self.assertTrue(formulario.is_valid(), formulario.errors)
        empresa = formulario.save()
        self.assertFalse(empresa.es_cliente)
        self.assertTrue(empresa.es_proveedor)

    def test_formulario_rechaza_empresa_sin_condicion(self):
        formulario = EmpresaFormulario(data=self.datos_formulario())

        self.assertFalse(formulario.is_valid())
        self.assertIn(
            'La empresa debe ser cliente, proveedora o ambas.',
            formulario.non_field_errors(),
        )

    def obtener_formulario_admin(self, datos, instancia=None):
        """Construye el formulario real que utiliza Django Admin."""
        solicitud = RequestFactory().post('/admin/empresas/empresa/')
        solicitud.user = self.usuario
        clase_formulario = EmpresaAdmin(Empresa, admin.site).get_form(
            solicitud, obj=instancia
        )
        return clase_formulario(data=datos, instance=instancia)

    def test_admin_permite_crear_empresa_con_ambas_condiciones(self):
        formulario = self.obtener_formulario_admin(
            self.datos_formulario(es_cliente=True, es_proveedor=True)
        )

        self.assertTrue(formulario.is_valid(), formulario.errors)

    def test_admin_rechaza_crear_empresa_sin_condicion(self):
        formulario = self.obtener_formulario_admin(self.datos_formulario())

        self.assertFalse(formulario.is_valid())
        self.assertIn(
            'La empresa debe ser cliente, proveedora o ambas.',
            formulario.non_field_errors(),
        )

    def test_admin_rechaza_editar_empresa_sin_condicion(self):
        formulario = self.obtener_formulario_admin(
            self.datos_formulario(
                razon_social=self.empresa.razon_social,
                ruc=self.empresa.ruc,
                email=self.empresa.email,
                telefono=self.empresa.telefono,
            ),
            instancia=self.empresa,
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn(
            'La empresa debe ser cliente, proveedora o ambas.',
            formulario.non_field_errors(),
        )

    def test_restriccion_de_base_rechaza_empresa_sin_condicion(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Empresa.objects.create(
                razon_social='Empresa inválida en base S.A.',
                ruc='80100004-4',
                email='invalida.base@example.com',
                telefono='021 100 004',
            )

    def test_validacion_comercial_conserva_validacion_del_ruc(self):
        formulario = EmpresaFormulario(
            data=self.datos_formulario(ruc='RUC-invalido', es_cliente=True)
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn('El formato del RUC no es válido.', formulario.errors['ruc'][0])
