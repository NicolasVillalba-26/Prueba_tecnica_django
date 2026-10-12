from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Lower, Trim


# Representa una división administrativa que agrupa varias ciudades.
class Departamento(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'departamento'
        verbose_name_plural = 'departamentos'

    def __str__(self):
        """Devuelve el nombre legible del departamento."""
        return self.nombre


# Representa una ciudad perteneciente a un único departamento.
class Ciudad(models.Model):
    nombre = models.CharField(max_length=100)
    # PROTECT evita eliminar departamentos que aún contienen ciudades.
    departamento = models.ForeignKey(
        Departamento,
        on_delete=models.PROTECT,
        related_name='ciudades',
    )

    class Meta:
        ordering = ['nombre']
        verbose_name = 'ciudad'
        verbose_name_plural = 'ciudades'
        constraints = [
            # Ignora mayúsculas y espacios exteriores al comparar nombres.
            models.UniqueConstraint(
                Lower(Trim('nombre')),
                'departamento',
                name='ciudad_unica_por_departamento',
            ),
        ]

    def clean(self):
        """Normaliza el nombre e impide duplicados dentro del departamento."""
        super().clean()
        self.nombre = (self.nombre or '').strip()
        if not self.nombre:
            raise ValidationError({'nombre': 'El nombre de la ciudad es obligatorio.'})

        ciudades_duplicadas = Ciudad.objects.filter(
            nombre__iexact=self.nombre,
            departamento_id=self.departamento_id,
        ).exclude(pk=self.pk)
        if ciudades_duplicadas.exists():
            raise ValidationError({
                'nombre': (
                    'La ciudad ya existe con este nombre en el departamento '
                    'seleccionado.'
                ),
            })

    def __str__(self):
        """Muestra la ciudad junto con su departamento."""
        return f'{self.nombre} ({self.departamento})'
