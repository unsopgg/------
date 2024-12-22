from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.core.mail import send_mail
from django.db import models
from gigaline.settings import EMAIL_HOST_USER


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password, *args, **kwargs):
        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)
        user.is_active = True
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, *args, **kwargs):
        email = self.normalize_email(email)
        user = self.model(email=email)
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save(using=self._db)
        return user


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=False)
    activation_code = models.CharField(max_length=100, blank=True)

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def create_activation_code(self):
        from django.utils.crypto import get_random_string
        code = get_random_string(6, '0123456789')
        self.activation_code = code
        self.save()

    def activate_with_code(self, activation_code):
        if self.activation_code != activation_code:
            raise Exception('Неверный код, проверь и попробуй снова')
        self.is_active = True
        self.activation_code = ''
        self.save()