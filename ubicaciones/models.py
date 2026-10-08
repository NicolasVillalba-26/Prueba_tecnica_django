from django.db import models


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
            # Un nombre puede repetirse únicamente en departamentos distintos.
            models.UniqueConstraint(
                fields=['nombre', 'departamento'],
                name='ciudad_unica_por_departamento',
            ),
        ]

    def __str__(self):
        """Muestra la ciudad junto con su departamento."""
        return f'{self.nombre} ({self.departamento})'
