from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from datetime import timedelta
import pytz
from devopspanel.core.models import Environment, ServiceGroup

class Permission(models.Model):
    name = models.CharField('Permission Name', max_length=100, unique=True)
    codename = models.CharField('Access Code', max_length=100, unique=True)
    description = models.TextField('Description', blank=True)
    view_name = models.CharField(
        'View Name',
        max_length=255,
        unique=True,
        help_text="Format: 'app_label:view_name' or 'app_label:*' for all views in an app."
    )

    def __str__(self):
        return self.name

class Role(models.Model):
    name = models.CharField('Role Name', max_length=100, unique=True)
    permissions = models.ManyToManyField('Permission', related_name='roles', blank=True)
    description = models.TextField('Description', blank=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    environments = models.ManyToManyField(
        Environment,
        related_name='users',
        blank=True,
        verbose_name='Environments'
    )
    service_groups = models.ManyToManyField(
        ServiceGroup,
        related_name='users',
        blank=True,
        verbose_name='Groups'
    )
    emergency_phone = models.CharField('Emergency Phone', max_length=20, blank=True, null=True)
    timezone = models.CharField(
        'Time Zone',
        max_length=50,
        choices=[(tz, tz) for tz in pytz.all_timezones],
        default='UTC'
    )
    roles = models.ManyToManyField(
        'Role',
        related_name='users',
        blank=True,
        verbose_name='Roles'
    )
    permissions = models.ManyToManyField(
        'Permission',
        related_name='users',
        blank=True
    )
    THEME_CHOICES = [
        ('light', 'Light Theme'),
        ('dark', 'Dark Theme'),
    ]
    theme_preference = models.CharField(
        'Theme preference',
        max_length=10,
        choices=THEME_CHOICES,
        default='light'
    )
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    last_activity = models.DateTimeField('Last Activity', null=True, blank=True)
    current_environment = models.ForeignKey(Environment, null=True, blank=True, on_delete=models.SET_NULL)

    def is_online(self):
        if self.last_activity:
            return timezone.now() - self.last_activity < timedelta(minutes=5)
        return False

    def get_permissions_set(self):
        role_permissions = Permission.objects.filter(roles__in=self.roles.all()).values_list('view_name', flat=True)
        direct_permissions = self.permissions.values_list('view_name', flat=True)
        return set(role_permissions) | set(direct_permissions)

    def get_all_permissions(self, obj=None):
        return {perm.replace(':', '.') for perm in self.get_permissions_set()}

    def has_perm(self, perm, obj=None):
        if self.is_superuser:
            return True
        return perm in self.get_all_permissions()

    def has_module_perms(self, app_label):
        if self.is_superuser:
            return True
        return any(p.startswith(f'{app_label}.') for p in self.get_all_permissions())

    def get_permissions(self):
        return self.get_permissions_set()
    def __str__(self):
        return self.username