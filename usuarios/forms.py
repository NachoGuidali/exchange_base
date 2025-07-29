from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, DepositoARS

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password1', 'password2', 'dni_frente', 'dni_dorso']


class DepositoARSForm(forms.ModelForm):
    class Meta:
        model = DepositoARS
        fields = ['monto', 'comprobante']
