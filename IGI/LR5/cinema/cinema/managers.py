from django.contrib.auth.base_user import BaseUserManager
from django.db import IntegrityError

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email должен быть указан')

        email = self.normalize_email(email)
        try:
            user = self.model(email=email, **extra_fields)
            user.set_password(password)
            user.save(using=self._db)
        except IntegrityError:
            raise ValueError('Пользователь с таким email уже существует')
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, password, **extra_fields)