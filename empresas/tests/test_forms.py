from django.test import TestCase

from empresas.forms import EmpresaFormulario


class EmpresaFormularioPruebas(TestCase):
    """Comprueba validaciones y exclusión de campos sensibles."""

    def test_no_expone_campos_de_auditoria(self):
        formulario = EmpresaFormulario()

        self.assertNotIn('usuario_creacion', formulario.fields)
        self.assertNotIn('usuario_modificacion', formulario.fields)
        self.assertNotIn('fecha_creacion', formulario.fields)
        self.assertNotIn('fecha_modificacion', formulario.fields)

    def test_rechaza_empresa_sin_rol_comercial(self):
        formulario = EmpresaFormulario(data={
            'razon_social': 'Empresa inválida',
            'ruc': '80000999-0',
            'email': 'empresa@example.com',
            'telefono': '021 000 000',
            'activo': True,
        })

        self.assertFalse(formulario.is_valid())
        self.assertIn('La empresa debe ser cliente', formulario.non_field_errors()[0])
