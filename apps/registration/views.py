from django.urls import reverse_lazy
from django.views import generic

from .forms import StudentCreationForm


class Register(generic.CreateView):
    form_class = StudentCreationForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'
