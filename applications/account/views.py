from django.shortcuts import render

from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import RegisterSerializer, LoginSerializer, ForgotPasswordSerializer, ForgotPasswordCompleteSerializer



class RegistrationView(APIView):
    def post(self, request):
        data = request.data
        serializers = RegisterSerializer(data=data)
        if serializers.is_valid(raise_exception=True):
            serializers.save()
            return Response('Вы успешно зарегистрировались!', status=status.HTTP_201_CREATED)


class ActivationView(APIView):
    def get(self, request, activation_code):
        user = get_object_or_404(User, activation_code=activation_code)
        user.is_active = True
        user.activation_code = ''
        user.save()
        return Response('Ваш аккаунт был успешно активирован', status=status.HTTP_200_OK)


class LoginView(ObtainAuthToken):
    serializer_class = LoginSerializer


class LogoutView(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request):
        user = request.user
        Token.objects.filter(user=user).delete()
        return Response('Вы успешно вышли из аккаунта', status=status.HTTP_200_OK)


class ForgotPasswordView(APIView):
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.send_verification_email()
            return Response("На вашу почту было выслано письмо")

class ForgotPasswordCompleteView(APIView):
    def post(self, request, verification_code):
        user = User.objects.get(activation_code=verification_code)
        user.activate_with_code(activation_code=verification_code)
        serializer = ForgotPasswordCompleteSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.set_new_password()
            return Response('Your password was updated!')