from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView


class VistaPrincipal(LoginRequiredMixin, TemplateView):
    """Muestra el punto de entrada protegido del sistema."""

    template_name = 'principal.html'
