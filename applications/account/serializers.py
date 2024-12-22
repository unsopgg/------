from django.contrib.auth import get_user_model, authenticate
from django.core.mail import send_mail
from rest_framework import serializers
from .tasks import send_activation_mail
from gigaline.settings import EMAIL_HOST_USER

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=True,
        min_length=2,
        max_length=50,
        error_messages={
            "required": "Имя пользователя обязательно для заполнения.",
            "min_length": "Имя пользователя должно содержать минимум 2 символа.",
            "max_length": "Имя пользователя не должно превышать 50 симв     лов."
        },
    )
    password = serializers.CharField(min_length=6, write_only=True)
    password_confirmation = serializers.CharField(min_length=6, write_only=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password_confirmation')

    def validate_email(self, email):
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Пользователь с таким мейлом уже существует')
        return email
    
    def validate_username(self, username):
        if not username.strip():
            raise serializers.ValidationError('Имя пользователя не может быть пустым или состоять только из пробелов.')
        return username

    def validate(self, validated_data):
        password = validated_data.get('password')
        password_confirmation = validated_data.get('password_confirmation')
        if password != password_confirmation:
            raise serializers.ValidationError("Пароли не совпадают")
        return validated_data

    def create(self, validated_data):
        email = validated_data.get('email')
        password = validated_data.get('password')
        username = validated_data.get('username')
        user = User.objects.create_user(email=email, username=username, password=password)
        send_activation_mail(user.email, user.activation_code)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(min_length=1)
    password = serializers.CharField(style= {'input_type':'password'}, trim_whitespace=False)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                msg = 'Невозможно войти в систему с предоставленными учетными данными'
                raise serializers.ValidationError(msg, code='authorization')

        else:
            msg = 'Должен включать "username" и "password"'
            raise serializers.ValidationError(msg, code='authorization')

        
        attrs['user'] = user
        return attrs


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, email):
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Такого пользователя не существует')
        return email

    def send_verification_email(self):
        email = self.validated_data.get('email')
        user = User.objects.get(email=email)
        user.create_activation_code()
        user.save()
        send_mail(
            'Password recovery',
            f"""Ваш код активации: http://localhost:8000/account/forgot_password_complete/{user.activation_code}""",
            EMAIL_HOST_USER,
            [user.email, ]
        )

class ForgotPasswordCompleteSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(min_length=6, required=True)
    password_confirmation = serializers.CharField(min_length=6, required=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password1 = attrs.get('password')
        password2 = attrs.get('password_confirmation')

        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Такого пользователя не существует')
        if password1 != password2:
            raise serializers.ValidationError('Пароли не совпадают')
        return attrs

    def set_new_password(self):
        email = self.validated_data.get('email')
        password = self.validated_data.get('password')
        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()