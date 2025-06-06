# users/mixins.py
from django.core.exceptions import PermissionDenied
from django.contrib.auth.mixins import AccessMixin

class RoleRequiredMixin(AccessMixin):

    required_roles = []     
    raise_exception = True   

    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return self.handle_no_permission()

        if user.is_superuser:
            return super().dispatch(request, *args, **kwargs)

        user_role_names = set(user.roles.values_list('name', flat=True))

        if not user_role_names.intersection(self.required_roles):
            if self.raise_exception:
                raise PermissionDenied("У вас нет прав для доступа к этой странице.")
            return self.handle_no_permission()

        return super().dispatch(request, *args, **kwargs)
