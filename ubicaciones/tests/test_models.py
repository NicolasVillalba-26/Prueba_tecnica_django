from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError
from django.test import TestCase

from ubicaciones.models import Ciudad, Departamento


class DepartamentoCiudadPruebas(TestCase):
    """Verifica relaciones y restricciones de departamentos y ciudades."""

    def test_crear_departamento(self):
        departamento = Departamento.objects.create(nombre='Central')

        self.assertEqual(str(departamento), 'Central')

    def test_crear_ciudad_asociada(self):
        departamento = Departamento.objects.create(nombre='Central')
        ciudad = Ciudad.objects.create(
            nombre='San Lorenzo',
            departamento=departamento,
        )

        self.assertIn(ciudad, departamento.ciudades.all())
        self.assertEqual(str(ciudad), 'San Lorenzo (Central)')

    def test_no_permite_ciudad_duplicada_en_departamento(self):
        departamento = Departamento.objects.create(nombre='Central')
        Ciudad.objects.create(nombre='San Lorenzo', departamento=departamento)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Ciudad.objects.create(
                nombre='San Lorenzo',
                departamento=departamento,
            )

    def test_permite_mismo_nombre_en_departamentos_distintos(self):
        primero = Departamento.objects.create(nombre='Central')
        segundo = Departamento.objects.create(nombre='Cordillera')

        Ciudad.objects.create(nombre='Nueva Colombia', departamento=primero)
        Ciudad.objects.create(nombre='Nueva Colombia', departamento=segundo)

        self.assertEqual(Ciudad.objects.filter(nombre='Nueva Colombia').count(), 2)

    def test_protege_departamento_con_ciudades(self):
        departamento = Departamento.objects.create(nombre='Central')
        Ciudad.objects.create(nombre='San Lorenzo', departamento=departamento)

        with self.assertRaises(ProtectedError):
            departamento.delete()
