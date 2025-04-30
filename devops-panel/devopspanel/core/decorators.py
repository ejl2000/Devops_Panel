from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from functools import wraps
from django.core.exceptions import PermissionDenied
from devopspanel.users.models import Permission

def permission_required(view_name):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"{reverse('login')}?next={request.path}")
            try:
                permission = Permission.objects.get(view_name=view_name)
            except Permission.DoesNotExist:
                raise PermissionDenied("Permission not found.")

            user_permissions = request.user.get_permissions()

            if permission.view_name in user_permissions:
                return view_func(request, *args, **kwargs)

            if ':' in view_name:
                app_label = view_name.split(':')[0]
                wildcard_permission = f"{app_label}:*"
                if wildcard_permission in user_permissions:
                    return view_func(request, *args, **kwargs)

            messages.error(request, "You do not have permission to access this page.")
            return redirect(reverse('dashboard:index'))

        return _wrapped_view
    return decorator


def any_permission_required(permissions):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            if any(request.user.has_perm(perm) for perm in permissions):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator