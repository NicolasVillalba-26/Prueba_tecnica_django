from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import RequestFactory, TestCase

from empresas.admin import EmpresaAdmin
from empresas.forms import EmpresaFormulario
from empresas.models import Empresa
from empresas.validadores import normalizar_ruc, validar_ruc


class ValidadorRucPruebas(TestCase):
    """Comprueba las reglas estructurales centralizadas del RUC."""

    def test_acepta_formato_correcto(self):
        validar_ruc('80012345-6')

    def test_rechaza_ruc_vacio(self):
        with self.assertRaisesMessage(ValidationError, 'El RUC es obligatorio.'):
            validar_ruc('   ')

    def test_rechaza_ruc_sin_guion(self):
        with self.assertRaises(ValidationError):
            validar_ruc('800123456')

    def test_rechaza_ruc_con_letras(self):
        with self.assertRaises(ValidationError):
            validar_ruc('800A2345-6')

    def test_rechaza_ruc_con_caracteres_especiales(self):
        with self.assertRaises(ValidationError):
            validar_ruc('80012.345-6')

    def test_rechaza_ruc_sin_digito_verificador(self):
        with self.assertRaises(ValidationError):
            validar_ruc('80012345-')

    def test_rechaza_mas_de_un_digito_verificador(self):
        with self.assertRaises(ValidationError):
            validar_ruc('80012345-67')

    def test_normaliza_espacios_exteriores(self):
        self.assertEqual(normalizar_ruc('  80012345-6  '), '80012345-6')
        validar_ruc('  80012345-6  ')


class IntegracionRucPruebas(TestCase):
    """Verifica formularios, modelo, unicidad y Django Admin."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_superuser(
            username='admin_ruc',
            email='admin.ruc@example.com',
            password='Clave-segura-2026',
        )
        cls.empresa = Empresa.objects.create(
            razon_social='Empresa existente S.A.',
            ruc='80012345-6',
            email='existente@example.com',
            telefono='021 123 456',
            es_cliente=True,
        )

    def datos_formulario(self, **cambios):
        datos = {
            'razon_social': 'Empresa nueva S.A.',
            'ruc': '80054321-0',
            'email': 'nueva@example.com',
            'telefono': '021 543 210',
            'es_cliente': True,
            'activo': True,
        }
        datos.update(cambios)
        return datos

    def test_formulario_aplica_validador_del_modelo(self):
        formulario = EmpresaFormulario(
            data=self.datos_formulario(ruc='RUC-invalido')
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn('El formato del RUC no es válido.', formulario.errors['ruc'][0])

    def test_formulario_normaliza_espacios(self):
        formulario = EmpresaFormulario(
            data=self.datos_formulario(ruc='  80054321-0  ')
        )

        self.assertTrue(formulario.is_valid(), formulario.errors)
        self.assertEqual(formulario.cleaned_data['ruc'], '80054321-0')

    def test_formulario_rechaza_ruc_duplicado(self):
        formulario = EmpresaFormulario(
            data=self.datos_formulario(ruc=self.empresa.ruc)
        )

        self.assertFalse(formulario.is_valid())
        self.assertEqual(
            formulario.errors['ruc'][0], 'El RUC ya se encuentra registrado.'
        )

    def test_edicion_conserva_el_ruc_propio(self):
        formulario = EmpresaFormulario(
            data=self.datos_formulario(
                razon_social=self.empresa.razon_social,
                ruc=self.empresa.ruc,
                email=self.empresa.email,
                telefono=self.empresa.telefono,
            ),
            instance=self.empresa,
        )

        self.assertTrue(formulario.is_valid(), formulario.errors)

    def test_edicion_rechaza_ruc_de_otra_empresa(self):
        otra_empresa = Empresa.objects.create(
            razon_social='Otra empresa S.A.',
            ruc='80099999-1',
            email='otra@example.com',
            telefono='021 999 999',
            es_proveedor=True,
        )
        formulario = EmpresaFormulario(
            data=self.datos_formulario(ruc=self.empresa.ruc),
            instance=otra_empresa,
        )

        self.assertFalse(formulario.is_valid())
        self.assertEqual(
            formulario.errors['ruc'][0], 'El RUC ya se encuentra registrado.'
        )

    def test_full_clean_normaliza_y_valida_ruc(self):
        empresa = Empresa(
            razon_social='Empresa normalizada S.A.',
            ruc='  80077777-2  ',
            email='normalizada@example.com',
            telefono='021 777 777',
            es_cliente=True,
        )

        empresa.full_clean()

        self.assertEqual(empresa.ruc, '80077777-2')

    def test_django_admin_aplica_el_mismo_validador(self):
        solicitud = RequestFactory().post('/admin/empresas/empresa/add/')
        solicitud.user = self.usuario
        clase_formulario = EmpresaAdmin(Empresa, admin.site).get_form(solicitud)
        formulario = clase_formulario(
            data=self.datos_formulario(ruc='80012345-X')
        )

        self.assertFalse(formulario.is_valid())
        self.assertIn('El formato del RUC no es válido.', formulario.errors['ruc'][0])
