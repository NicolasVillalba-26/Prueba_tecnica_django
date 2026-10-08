from django.contrib.auth.forms import AuthenticationForm
from django.forms import PasswordInput, TextInput


class FormularioInicioSesion(AuthenticationForm):
    """Presenta las credenciales nativas de Django con textos en español."""

    error_messages = {
        'invalid_login': 'Usuario o contraseña incorrectos.',
        'inactive': 'Esta cuenta se encuentra inactiva.',
    }

    def __init__(self, *args, **kwargs):
        """Aplica etiquetas y estilos sin alterar la validación de Django."""
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuario'
        self.fields['username'].widget = TextInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ingrese su usuario',
                'autocomplete': 'username',
                'autofocus': True,
            }
        )
        self.fields['password'].label = 'Contraseña'
        self.fields['password'].widget = PasswordInput(
            attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ingrese su contraseña',
                'autocomplete': 'current-password',
            }
        )
