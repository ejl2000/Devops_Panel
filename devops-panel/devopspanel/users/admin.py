# users/admin.py

from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, Permission, Role
from devopspanel.users.forms import UserChangeForm, UserCreationForm

User = get_user_model()

@admin.register(CustomUser)
class CustomUserAdmin(auth_admin.UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "avatar", "emergency_phone", "timezone")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "roles",
                    "permissions",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "last_activity")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "is_staff", "is_superuser"),
        }),
    )
    list_display = ["username", "first_name", "last_name", "email", "is_superuser"]
    search_fields = ["first_name", "last_name", "email", "username"]
    ordering = ["username"]

@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['name', 'codename', 'view_name']
    search_fields = ['name', 'codename', 'view_name']

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['name', 'description']
    search_fields = ['name', 'description']