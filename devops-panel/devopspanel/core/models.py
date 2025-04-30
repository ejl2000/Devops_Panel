from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import pytz
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import Permission as BasePermission
import uuid

def user_directory_path(instance, filename):
    return f'user_{instance.id}/{filename}'

class CodeBase(models.Model):
    name = models.CharField('Code Base Name', max_length=255)
    url = models.URLField('Repository URL')
    created_at = models.DateTimeField('Created At', auto_now_add=True)

    class Meta:
        verbose_name = 'CodeBase'
        verbose_name_plural = 'CodeBases'

    def __str__(self):
        return self.name

class CodeBaseDependency(models.Model):
    code_base = models.ForeignKey(
        CodeBase,
        on_delete=models.CASCADE,
        related_name='dependencies',
        verbose_name='Code Base'
    )
    name = models.CharField('Dependency Name', max_length=255)
    url = models.URLField('Dependency URL')
    dependencies = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='dependents')

    def __str__(self):
        return f"{self.name} (Dependency of {self.code_base.name})"

class Environment(models.Model):
    name = models.CharField('Environment Name', max_length=100, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Created by',
        related_name='created_environments'
    )
    created_at = models.DateTimeField('Creation date', auto_now_add=True)

    class Meta:
        verbose_name = 'Environment'
        verbose_name_plural = 'Environments'

    def __str__(self):
        return self.name

class ServiceGroup(models.Model):
    name = models.CharField('Group Name', max_length=100)
    environment = models.ForeignKey(
        'Environment',
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name='Environment',
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Created by'
    )
    created_at = models.DateTimeField('Creation Date', auto_now_add=True)

    class Meta:
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'
        unique_together = ('name', 'environment')

    def __str__(self):
        return f"{self.name} ({self.environment.name})" if self.environment else self.name

class SubGroup(models.Model):
    name = models.CharField('SubGroup Name', max_length=100)
    group = models.ForeignKey(
        'ServiceGroup',
        on_delete=models.CASCADE,
        related_name='subgroups',
        verbose_name='Group'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Created by'
    )
    created_at = models.DateTimeField('Creation Date', auto_now_add=True)

    class Meta:
        verbose_name = 'SubGroup'
        verbose_name_plural = 'SubGroups'

    def __str__(self):
        return f"{self.name} ({self.group.name})"

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['name']

    def __str__(self):
        return self.name

class ServiceButton(models.Model):
    LOCATION_CHOICES = [
        ('K8S', 'K8S'),
        ('VM-GCP', 'VM-GCP'),
        ('Bare-Metal', 'Bare-Metal'),
        ('Cloud-SQL', 'Cloud-SQL'),
        ('CloudFlare', 'CloudFlare'),
    ]
    DEV_LANGUAGE_CHOICES = [
        ('Python', 'Python'),
        ('Java', 'Java'),
        ('C++', 'C++'),
        ('C#', 'C#'),
        ('JavaScript', 'JavaScript'),
        ('Ruby', 'Ruby'),
        ('PHP', 'PHP'),
        ('Go', 'Go'),
        ('Swift', 'Swift'),
        ('Kotlin', 'Kotlin'),
        ('Perl', 'Perl'),
        ('Rust', 'Rust'),
        ('Scala', 'Scala'),
        ('Objective-C', 'Objective-C'),
        ('Dart', 'Dart'),
        ('TypeScript', 'TypeScript'),
        ('Elixir', 'Elixir'),
        ('Haskell', 'Haskell'),
        ('Lua', 'Lua'),
        ('Erlang', 'Erlang'),
        ('Matlab', 'Matlab'),
        ('SQL', 'SQL'),
        ('PL/SQL', 'PL/SQL'),
        ('T-SQL', 'T-SQL'),
        ('MySQL', 'MySQL'),
        ('PostgreSQL', 'PostgreSQL'),
        ('MongoDB', 'MongoDB'),
        ('SQLite', 'SQLite'),
        ('Redis', 'Redis'),
        ('Cassandra', 'Cassandra'),
        ('MariaDB', 'MariaDB'),
        ('Oracle', 'Oracle'),
    ]

    name = models.CharField('Name', max_length=100)
    description = models.TextField('Description', blank=True)
    url = models.URLField('URL', blank=True, null=True)
    icon_choice = models.CharField('Icon (choose)', max_length=100, blank=True)
    custom_icon = models.ImageField('Icon (User\'s)', upload_to=user_directory_path, blank=True, null=True)
    groups = models.ManyToManyField(
        'ServiceGroup',
        related_name='buttons',
        blank=True,
        verbose_name='Groups'
    )
    subgroup = models.ForeignKey(
        'SubGroup',
        on_delete=models.CASCADE,
        related_name='buttons',
        verbose_name='SubGroup',
        null=True,
        blank=True
    )
    environment = models.ForeignKey(
        'Environment',
        on_delete=models.CASCADE,
        related_name='buttons',
        verbose_name='Environment',
        null=True,
        blank=True
    )
    tags = models.ManyToManyField(Tag, related_name='service_buttons', blank=True)
    connections = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='connected_to',
        verbose_name='Connections'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='Created by'
    )
    executive = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='executive_buttons',
        verbose_name='Executive'
    )
    code_base = models.ForeignKey(
        CodeBase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_buttons',
        verbose_name='Code Base'
    )
    dev_language = models.CharField(
        'Development Language',
        max_length=50,
        choices=DEV_LANGUAGE_CHOICES,
        null=True,
        blank=True
    )
    ip = models.GenericIPAddressField('IP Address', blank=True, null=True)
    port = models.PositiveIntegerField('Port', blank=True, null=True)
    version = models.CharField('Version', max_length=50, blank=True, null=True)
    location = models.CharField('Location', max_length=20, choices=LOCATION_CHOICES, default='VM-GCP')
    is_multi_link = models.BooleanField('Is Multi-Link', default=False)
    created_at = models.DateTimeField('Creation Date', auto_now_add=True)

    class Meta:
        verbose_name = 'Service Button'
        verbose_name_plural = 'Service Buttons'
        unique_together = ('name', 'environment')

    def __str__(self):
        return self.name

class ServiceButtonLink(models.Model):
    service_button = models.ForeignKey(
        ServiceButton,
        on_delete=models.CASCADE,
        related_name='links',
        verbose_name='Service Button'
    )
    name = models.CharField('Link Name', max_length=100)
    url = models.URLField('URL')
    location = models.CharField('Location', max_length=20, choices=ServiceButton.LOCATION_CHOICES, default='VM-GCP')

    class Meta:
        verbose_name = 'Service Button Link'
        verbose_name_plural = 'Service Button Links'

    def __str__(self):
        return f"{self.name} ({self.location})"


class BearerToken(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('revoked', 'Revoked'),
    ]

    token = models.CharField(max_length=255, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')

    def is_expired(self):
        return timezone.now() >= self.expires_at

    def __str__(self):
        return f"Token for {self.user.username}, Expires at {self.expires_at}, Status: {self.status}"


class ServiceButtonIP(models.Model):
    service_button = models.ForeignKey(
        ServiceButton,
        on_delete=models.CASCADE,  # Важно!
        related_name='ips',
        verbose_name='Service Button'
    )
    ip_address = models.GenericIPAddressField()

    def __str__(self):
        return self.ip_address

class Maintenance(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('canceled', 'Canceled'),
        ('completed', 'Completed'),
        ('partially_completed', 'Partially Completed'),
    ]

    title = models.CharField('Title', max_length=255)
    description = models.TextField('Description', blank=True, null=True)
    start_time = models.DateTimeField('Start Time')
    end_time = models.DateTimeField('End Time')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='maintenances_created',
        verbose_name='Created By'
    )
    executive = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='maintenances_executive',
        verbose_name='Executive',
        null=True,
        blank=True
    )
    service_buttons = models.ManyToManyField(
        'ServiceButton',
        related_name='maintenances',
        blank=True,
        verbose_name='Service Buttons'
    )
    created_at = models.DateTimeField('Created At', auto_now_add=True)
    updated_at = models.DateTimeField('Updated At', auto_now=True)

    class Meta:
        verbose_name = 'Maintenance'
        verbose_name_plural = 'Maintenances'
        ordering = ['-start_time']
        permissions = [
            ('manage_maintenance', 'Can manage maintenance events'),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"