from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, DepositoARS, DepositoUSDT

class RegistroUsuarioForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password1', 'password2', 'dni_frente', 'dni_dorso']


class DepositoARSForm(forms.ModelForm):
    class Meta:
        model = DepositoARS
        fields = ['monto', 'comprobante']

class DepositoUSDTForm(forms.ModelForm):
    class Meta:
        model = DepositoUSDT
        fields = ['monto', 'red', 'txid', 'comprobante']
        widgets = {
            'monto': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }