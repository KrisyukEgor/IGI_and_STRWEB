from django.apps import AppConfig
from django.db.models.signals import post_migrate

def create_roles(sender, **kwargs):
    from .models import Role
    roles = [
        ('cashier', 'Кассир'),
        ('user', 'Обычный пользователь'),
        ('admin', 'Администратор'),
    ]
    for role in roles:
        Role.objects.get_or_create(name=role[0])

class CinemaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cinema'

    def ready(self):
        post_migrate.connect(create_roles, sender=self)