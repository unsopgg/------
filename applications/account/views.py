from django.shortcuts import render, redirect
from rest_framework.authtoken.models import Token
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication

class RegistrationView(APIView):
    def get(self, request):
        # Возвращаем форму для регистрации при GET запросе
        return render(request, 'register.html')

    def post(self, request):
        data = request.POST
        serializer = RegisterSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            # После успешной регистрации редирект на страницу входа
            return redirect('login')  # Перенаправление на страницу входа
        return render(request, 'register.html', {'errors': serializer.errors})


class LoginView(APIView):
    def get(self, request):
        # Возвращаем форму для входа при GET запросе
        return render(request, 'login.html')

    def post(self, request):
        data = request.POST
        serializer = LoginSerializer(data=data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token = Token.objects.get_or_create(user=user)[0]
            # Сохраняем токен в сессии
            request.session['token'] = token.key
            print(request.session['token'])
            # Перенаправляем на главную страницу
            return redirect('index')  # Перенаправление на главную страницу
        return render(request, 'login.html', {'errors': serializer.errors})



class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        return render(request, "logout.html")

    def post(self, request):
        user = request.user
        Token.objects.filter(user=user).delete()
        return redirect('login')


class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.send_verification_email()
            return Response("На вашу почту было выслано письмо")

class ForgotPasswordCompleteView(APIView):
    def get(self, request, verification_code):
        # Отправляем verification_code в шаблон
        return render(request, 'forgot_password_complete.html', {'verification_code': verification_code})

    def post(self, request, verification_code):
        user = User.objects.get(activation_code=verification_code)
        user.activate_with_code(activation_code=verification_code)
        serializer = ForgotPasswordCompleteSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.set_new_password()
            return redirect('login')

class ActivationView(APIView):
    def get(self, request, activation_code):
        user = get_object_or_404(User, activation_code=activation_code)
        user.is_active = True
        user.activation_code = ''
        user.save()
        return render(request, 'activation.html')
    
class HomeView(APIView):
    def get(self, request):
        # Проверка токена в сессии
        token_key = request.session.get('token')
        if token_key:
            try:
                token = Token.objects.get(key=token_key)
                user = token.user
                # Проводим какие-то операции с аутентифицированным пользователем
            except Token.DoesNotExist:
                return Response({"message": "Пользователь не аутентифицирован"}, status=401)
        else:
            return Response({"message": "Токен не найден в сессии"}, status=401)

        return Response({"message": "Добро пожаловать, аутентифицированный пользователь!"})

class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [SessionAuthentication, TokenAuthentication]

    def get(self, request):
        return Response({"message": "Вы аутентифицированы"})