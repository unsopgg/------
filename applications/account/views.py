from django.shortcuts import render, redirect, get_object_or_404
from .forms import *
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from .models import User
from .serializers import *

def login_view(request):
    if request.method == "POST":
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')

            # Аутентификация пользователя по email с передачей объекта запроса
            user = authenticate(request, email=email, password=password)

            if user is not None and user.is_active:
                login(request, user)
                return redirect('index')
            else:
                form.add_error(None, "Неверная электронная почта или пароль.")
    else:
        form = EmailLoginForm()

    return render(request, 'login.html', {'form': form})


def registration_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()  # Создаём нового пользователя
            messages.success(request, 'Регистрация прошла успешно!')
            return redirect('login')  # Перенаправление на страницу входа
        else:
            # Если форма невалидна, отображаем ошибки
            messages.error(request, 'Исправьте ошибки в форме.')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('/')



def activation_view(request, activation_code):
    # Получаем пользователя с указанным activation_code
    user = get_object_or_404(User, activation_code=activation_code)

    # Активируем пользователя
    user.is_active = True
    user.activation_code = ''
    user.save()

    # Возвращаем страницу с подтверждением активации
    return render(request, 'activation.html')