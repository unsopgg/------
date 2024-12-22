# forms.py
from django import forms
from .models import User
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate

class RegisterForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Подтвердите пароль")

    class Meta:
        model = User
        fields = ['email', 'password', 'password_confirm']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        if password != password_confirm:
            raise forms.ValidationError("Пароли не совпадают!")
        return cleaned_data

class EmailLoginForm(forms.Form):
    email = forms.EmailField(label="Электронная почта", widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"}))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        password = cleaned_data.get("password")

        if email and password:
            # Попытка аутентифицировать пользователя по email
            user = authenticate(email=email, password=password)
            if user is None:
                raise forms.ValidationError("Неверная электронная почта или пароль.")
            if not user.is_active:
                raise forms.ValidationError("Пользователь не активирован.")
        return cleaned_data