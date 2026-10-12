from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import RequestFactory, TestCase

from ubicaciones.admin import CiudadAdmin
from ubicaciones.forms import CiudadFormulario
from ubicaciones.models import Ciudad, Departamento


class ValidacionCiudadPruebas(TestCase):
    """Verifica nombres únicos por departamento en todas las capas."""

    @classmethod
    def setUpTestData(cls):
        cls.usuario = get_user_model().objects.create_superuser(
            username='admin_ciudades',
            email='admin.ciudades@example.com',
            password='Clave-segura-2026',
        )
        cls.central = Departamento.objects.create(nombre='Central')
        cls.cordillera = Departamento.objects.create(nombre='Cordillera')
        cls.atyra = Ciudad.objects.create(
            nombre='Atyrá', departamento=cls.cordillera
        )
        cls.caacupe = Ciudad.objects.create(
            nombre='Caacupé', departamento=cls.cordillera
        )

    def test_crea_ciudad_valida(self):
        ciudad = Ciudad(nombre='Luque', departamento=self.central)

        ciudad.full_clean()
        ciudad.save()

        self.assertTrue(Ciudad.objects.filter(pk=ciudad.pk).exists())

    def test_rechaza_duplicado_en_mismo_departamento(self):
        ciudad = Ciudad(nombre='Atyrá', departamento=self.cordillera)

        with self.assertRaisesMessage(
            ValidationError,
            'La ciudad ya existe con este nombre en el departamento seleccionado.',
        ):
            ciudad.full_clean()

    def test_permite_mismo_nombre_en_departamentos_distintos(self):
        ciudad = Ciudad(nombre='Atyrá', departamento=self.central)

        ciudad.full_clean()
        ciudad.save()

        self.assertEqual(Ciudad.objects.filter(nombre='Atyrá').count(), 2)

    def test_rechaza_nombre_vacio(self):
        ciudad = Ciudad(nombre='', departamento=self.central)

        with self.assertRaises(ValidationError):
            ciudad.full_clean()

    def test_rechaza_nombre_compuesto_solo_por_espacios(self):
        ciudad = Ciudad(nombre='   ', departamento=self.central)

        with self.assertRaisesMessage(
            ValidationError, 'El nombre de la ciudad es obligatorio.'
        ):
            ciudad.full_clean()

    def test_normaliza_espacios_exteriores(self):
        ciudad = Ciudad(nombre='  Luque  ', departamento=self.central)

        ciudad.full_clean()

        self.assertEqual(ciudad.nombre, 'Luque')

    def test_rechaza_duplicado_sin_distinguir_mayusculas(self):
        ciudad = Ciudad(nombre='ATYRÁ', departamento=self.cordillera)

        with self.assertRaises(ValidationError):
            ciudad.full_clean()

    def test_edicion_conserva_nombre_y_departamento_propios(self):
        self.atyra.full_clean()
        self.atyra.save()

        self.assertEqual(self.atyra.nombre, 'Atyrá')

    def test_edicion_rechaza_nombre_de_otra_ciudad(self):
        self.atyra.nombre = 'Caacupé'

        with self.assertRaises(ValidationError):
            self.atyra.full_clean()

    def test_cambio_de_departamento_rechaza_duplicado(self):
        ciudad_central = Ciudad.objects.create(
            nombre='Atyrá', departamento=self.central
        )
        ciudad_central.departamento = self.cordillera

        with self.assertRaises(ValidationError):
            ciudad_central.full_clean()

    def test_formulario_muestra_error_comprensible(self):
        formulario = CiudadFormulario(data={
            'nombre': 'atyrá',
            'departamento': self.cordillera.pk,
        })

        self.assertFalse(formulario.is_valid())
        self.assertEqual(
            formulario.errors['nombre'][0],
            'La ciudad ya existe con este nombre en el departamento seleccionado.',
        )

    def test_formulario_de_edicion_excluye_la_propia_instancia(self):
        formulario = CiudadFormulario(
            data={
                'nombre': '  Atyrá  ',
                'departamento': self.cordillera.pk,
            },
            instance=self.atyra,
        )

        self.assertTrue(formulario.is_valid(), formulario.errors)
        self.assertEqual(formulario.cleaned_data['nombre'], 'Atyrá')

    def test_django_admin_utiliza_la_validacion_del_modelo(self):
        solicitud = RequestFactory().post('/admin/ubicaciones/ciudad/add/')
        solicitud.user = self.usuario
        clase_formulario = CiudadAdmin(Ciudad, admin.site).get_form(solicitud)
        formulario = clase_formulario(data={
            'nombre': 'ATYRÁ',
            'departamento': self.cordillera.pk,
        })

        self.assertFalse(formulario.is_valid())
        self.assertEqual(
            formulario.errors['nombre'][0],
            'La ciudad ya existe con este nombre en el departamento seleccionado.',
        )

    def test_postgresql_rechaza_duplicado_sin_distinguir_mayusculas(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Ciudad.objects.create(
                nombre='ATYRÁ', departamento=self.cordillera
            )

    def test_postgresql_rechaza_duplicado_con_espacios_exteriores(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Ciudad.objects.create(
                nombre='  Atyrá  ', departamento=self.cordillera
            )
