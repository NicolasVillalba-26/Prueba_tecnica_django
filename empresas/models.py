from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from ubicaciones.models import Ciudad

from .validadores import normalizar_ruc, validar_ruc


class Categoria(models.Model):
    """Clasifica empresas según su actividad o función comercial."""

    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()

    class Meta:
        ordering = ['nombre']
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        """Devuelve el nombre visible de la categoría."""
        return self.nombre


class Empresa(models.Model):
    """Representa una organización cliente, proveedora o ambas."""

    razon_social = models.CharField('razón social', max_length=200)
    # El validador comprueba la estructura; la base de datos garantiza unicidad.
    ruc = models.CharField(
        'RUC', max_length=30, unique=True, validators=[validar_ruc]
    )
    email = models.EmailField('correo electrónico')
    telefono = models.CharField('teléfono', max_length=30)
    es_cliente = models.BooleanField('es cliente', default=False)
    es_proveedor = models.BooleanField('es proveedor', default=False)
    activo = models.BooleanField(default=True)
    categorias = models.ManyToManyField(
        Categoria,
        related_name='empresas',
        blank=True,
    )
    fecha_creacion = models.DateTimeField('fecha de creación', auto_now_add=True)
    fecha_modificacion = models.DateTimeField('fecha de modificación', auto_now=True)
    # SET_NULL conserva la empresa y su historial si se elimina un usuario.
    usuario_creacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='empresas_creadas',
        null=True,
        blank=True,
        editable=False,
    )
    usuario_modificacion = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='empresas_modificadas',
        null=True,
        blank=True,
        editable=False,
    )

    class Meta:
        ordering = ['razon_social']
        verbose_name = 'empresa'
        verbose_name_plural = 'empresas'
        constraints = [
            # Toda empresa debe participar al menos en un rol comercial.
            models.CheckConstraint(
                condition=Q(es_cliente=True) | Q(es_proveedor=True),
                name='empresa_debe_ser_cliente_o_proveedor',
                violation_error_message=(
                    'La empresa debe ser cliente, proveedora o ambas.'
                ),
            ),
        ]

    def clean(self):
        """Valida las reglas comerciales antes de usar formularios o Admin."""
        self.ruc = normalizar_ruc(self.ruc)
        super().clean()
        if not self.es_cliente and not self.es_proveedor:
            raise ValidationError(
                'La empresa debe ser cliente, proveedora o ambas.'
            )

    def __str__(self):
        """Muestra la razón social junto con el RUC."""
        return f'{self.razon_social} ({self.ruc})'


class Contacto(models.Model):
    """Representa una persona vinculada con una empresa."""

    # CASCADE elimina contactos que dejan de tener una empresa propietaria.
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name='contactos',
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField('correo electrónico')
    telefono = models.CharField('teléfono', max_length=30)
    cargo = models.CharField(max_length=100)

    class Meta:
        ordering = ['apellido', 'nombre']
        verbose_name = 'contacto'
        verbose_name_plural = 'contactos'

    def __str__(self):
        """Devuelve el nombre completo y la empresa del contacto."""
        return f'{self.nombre} {self.apellido} - {self.empresa.razon_social}'


class Direccion(models.Model):
    """Almacena una dirección postal perteneciente a un contacto."""

    class Tipo(models.TextChoices):
        LABORAL = 'LABORAL', 'Laboral'
        PARTICULAR = 'PARTICULAR', 'Particular'
        FACTURACION = 'FACTURACION', 'Facturación'
        OTRO = 'OTRO', 'Otro'

    # CASCADE mantiene el ciclo de vida de las direcciones unido al contacto.
    contacto = models.ForeignKey(
        Contacto,
        on_delete=models.CASCADE,
        related_name='direcciones',
    )
    direccion = models.CharField('dirección', max_length=255)
    codigo_postal = models.CharField('código postal', max_length=20)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    # PROTECT impide eliminar ciudades que todavía se usan en direcciones.
    ciudad = models.ForeignKey(
        Ciudad,
        on_delete=models.PROTECT,
        related_name='direcciones',
    )

    class Meta:
        ordering = ['contacto', 'tipo', 'direccion']
        verbose_name = 'dirección'
        verbose_name_plural = 'direcciones'

    def __str__(self):
        """Muestra el tipo, la dirección y la ciudad asociada."""
        return f'{self.get_tipo_display()}: {self.direccion}, {self.ciudad}'
