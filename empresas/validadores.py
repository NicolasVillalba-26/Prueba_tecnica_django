import re

from django.core.exceptions import ValidationError


PATRON_RUC = re.compile(r'^[0-9]+-[0-9]$')


def normalizar_ruc(valor):
    """Elimina los espacios exteriores sin alterar el identificador fiscal."""
    if not isinstance(valor, str):
        return valor
    return valor.strip()


def validar_ruc(valor):
    """Valida la estructura ``número-dígito`` del RUC paraguayo.

    Esta validación es estructural. No comprueba matemáticamente el dígito
    verificador porque no se incorporó un algoritmo sin una especificación
    técnica oficial completa y verificable.
    """
    ruc = normalizar_ruc(valor)
    if not ruc:
        raise ValidationError('El RUC es obligatorio.', code='ruc_obligatorio')
    if not PATRON_RUC.fullmatch(ruc):
        raise ValidationError(
            'El formato del RUC no es válido. Utilice números, un guion y un '
            'único dígito verificador, por ejemplo: 80012345-6.',
            code='ruc_formato_invalido',
        )
