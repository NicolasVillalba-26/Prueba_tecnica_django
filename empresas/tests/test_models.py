from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from empresas.models import Categoria, Contacto, Direccion, Empresa
from ubicaciones.models import Ciudad, Departamento


class EmpresaModelosPruebas(TestCase):
    """Verifica modelos, reglas comerciales y relaciones empresariales."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_user(
            username='auditor',
            password='clave-segura-pruebas',
        )
        cls.departamento = Departamento.objects.create(nombre='Central')
        cls.ciudad = Ciudad.objects.create(
            nombre='Asunción',
            departamento=cls.departamento,
        )

    def crear_empresa(self, ruc='80000001-0', **valores):
        """Crea una empresa válida para reutilizarla en las pruebas."""
        datos = {
            'razon_social': 'Empresa de Prueba S.A.',
            'ruc': ruc,
            'email': 'empresa@example.com',
            'telefono': '021 555 000',
            'es_cliente': True,
        }
        datos.update(valores)
        return Empresa.objects.create(**datos)

    def test_crear_empresa(self):
        empresa = self.crear_empresa()

        self.assertTrue(empresa.es_cliente)
        self.assertFalse(empresa.es_proveedor)
        self.assertTrue(empresa.activo)
        self.assertIsNotNone(empresa.fecha_creacion)

    def test_ruc_debe_ser_unico(self):
        self.crear_empresa()

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.crear_empresa(email='otra@example.com')

    def test_asociar_multiples_categorias(self):
        empresa = self.crear_empresa()
        primera = Categoria.objects.create(nombre='Tecnología')
        segunda = Categoria.objects.create(nombre='Servicios')

        empresa.categorias.add(primera, segunda)

        self.assertEqual(empresa.categorias.count(), 2)
        self.assertIn(empresa, primera.empresas.all())

    def test_asociar_contacto(self):
        empresa = self.crear_empresa()
        contacto = Contacto.objects.create(
            empresa=empresa,
            nombre='Ana',
            apellido='Gómez',
            email='ana@example.com',
            telefono='0981 000 000',
            cargo='Gerente',
        )

        self.assertIn(contacto, empresa.contactos.all())

    def test_asociar_multiples_direcciones_a_contacto(self):
        empresa = self.crear_empresa()
        contacto = Contacto.objects.create(
            empresa=empresa,
            nombre='Ana',
            apellido='Gómez',
            email='ana@example.com',
            telefono='0981 000 000',
            cargo='Gerente',
        )
        Direccion.objects.create(
            contacto=contacto,
            direccion='Avenida Principal 123',
            codigo_postal='1209',
            tipo=Direccion.Tipo.LABORAL,
            ciudad=self.ciudad,
        )
        Direccion.objects.create(
            contacto=contacto,
            direccion='Calle Secundaria 456',
            codigo_postal='1209',
            tipo=Direccion.Tipo.PARTICULAR,
            ciudad=self.ciudad,
        )

        self.assertEqual(contacto.direcciones.count(), 2)

    def test_empresa_debe_ser_cliente_o_proveedor(self):
        empresa = Empresa(
            razon_social='Empresa sin rol',
            ruc='80000002-0',
            email='sinrol@example.com',
            telefono='021 555 001',
        )

        with self.assertRaisesMessage(
            ValidationError,
            'La empresa debe ser cliente, proveedora o ambas.',
        ):
            empresa.full_clean()

    def test_restriccion_de_base_exige_rol_comercial(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Empresa.objects.create(
                razon_social='Empresa sin rol',
                ruc='80000003-0',
                email='sinrol@example.com',
                telefono='021 555 002',
            )

    def test_valida_correo_electronico(self):
        empresa = Empresa(
            razon_social='Empresa con correo inválido',
            ruc='80000004-0',
            email='correo-invalido',
            telefono='021 555 003',
            es_proveedor=True,
        )

        with self.assertRaises(ValidationError):
            empresa.full_clean()

    def test_valida_tipo_de_direccion(self):
        empresa = self.crear_empresa()
        contacto = Contacto.objects.create(
            empresa=empresa,
            nombre='Ana',
            apellido='Gómez',
            email='ana@example.com',
            telefono='0981 000 000',
            cargo='Gerente',
        )
        direccion = Direccion(
            contacto=contacto,
            direccion='Avenida Principal 123',
            codigo_postal='1209',
            tipo='TIPO_INVALIDO',
            ciudad=self.ciudad,
        )

        with self.assertRaises(ValidationError):
            direccion.full_clean()
