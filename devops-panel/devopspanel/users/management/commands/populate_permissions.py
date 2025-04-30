import string
import random
from django.core.management.base import BaseCommand
from django.urls import get_resolver, URLPattern, URLResolver
from devopspanel.users.models import Permission, Role, CustomUser
from django.contrib.auth import get_user_model
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Populate Permissions based on existing views, including wildcard Permissions for each app. Also create standard roles and assign them to superuser.'

    def handle(self, *args, **options):
        resolver = get_resolver()
        views = self.get_all_view_names(resolver)

        created_count = 0
        all_permissions = []

        for view_name in views:
            name = f"Access to {view_name}"
            codename = view_name.replace(':', '__')
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    'name': name,
                    'view_name': view_name
                }
            )
            if created:
                created_count += 1
                logger.info(f"Created Permission: {name}")
            else:
                if permission.view_name != view_name:
                    logger.warning(f"Permission '{name}' exists with different view_name. Existing view_name: '{permission.view_name}', New view_name: '{view_name}'. Skipping update.")
                else:
                    logger.debug(f"Permission already exists: {name}")
            all_permissions.append(permission)

        app_labels = {view_name.split(':')[0] for view_name in views if ':' in view_name}
        for app_label in app_labels:
            wildcard_view_name = f"{app_label}:*"
            name = f"All Permissions for {app_label}"
            codename = f"{app_label}__all"
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    'name': name,
                    'view_name': wildcard_view_name
                }
            )
            if created:
                created_count += 1
                logger.info(f"Created Wildcard Permission: {name}")
            else:
                if permission.view_name != wildcard_view_name:
                    logger.warning(f"Wildcard Permission '{name}' exists with different view_name. Existing view_name: '{permission.view_name}', New view_name: '{wildcard_view_name}'. Skipping update.")
                else:
                    logger.debug(f"Wildcard Permission already exists: {name}")
            all_permissions.append(permission)

        field_permissions = [
            {"name": "Can edit description", "codename": "can_edit_description",
             "view_name": "core:edit_servicebutton_description"},
            {"name": "Can edit tags", "codename": "can_edit_tags", "view_name": "core:edit_servicebutton_tags"},
            {"name": "Can edit repository", "codename": "can_edit_repository",
             "view_name": "core:edit_servicebutton_repository"},
            {"name": "Can edit port", "codename": "can_edit_port", "view_name": "core:edit_servicebutton_port"},
            {"name": "Can edit version", "codename": "can_edit_version",
             "view_name": "core:edit_servicebutton_version"},
            {"name": "Can edit URL", "codename": "edit_servicebutton_url",
             "view_name": "core:edit_servicebutton_url"},
            {"name": "Can edit Icon (choice/custom)", "codename": "edit_servicebutton_icon",
             "view_name": "core:edit_servicebutton_icon"},
            {"name": "Can edit Groups/SubGroups", "codename": "edit_servicebutton_groups",
             "view_name": "core:edit_servicebutton_groups"},
            {"name": "Can edit Location", "codename": "edit_servicebutton_location",
             "view_name": "core:edit_servicebutton_location"},
            {"name": "Can edit Connections", "codename": "edit_servicebutton_connections",
             "view_name": "core:edit_servicebutton_connections"},
            {"name": "Can edit Executive", "codename": "edit_servicebutton_executive",
             "view_name": "core:edit_servicebutton_executive"},
            {"name": "Can edit custom Icon", "codename": "edit_servicebutton_custom_icon",
             "view_name": "core:edit_servicebutton_custom_icon"},
            {"name": "Can edit dev language", "codename": "edit_servicebutton_dev_language",
             "view_name": "core:edit_servicebutton_dev_language"},
            {"name": "Can edit Permissions", "codename": "edit_users_permissions",
             "view_name": "users:permission_editor"},
            {"name": "Can edit Roles", "codename": "edit_users_roles",
             "view_name": "users:roles_editor"},
            {"name": "Can edit Users", "codename": "edit_users",
             "view_name": "users:editor"},
            {"name": "Can view all", "codename": "viewer",
             "view_name": "core:viewer"},
            {"name": "Can Edit all", "codename": "editor",
             "view_name": "core:editor"},
            {"name": "Can Manage API Tokens", "codename": "api",
             "view_name": "core:api"},

            {"name": "Can Manage Tags", "codename": "core.manage_tags",
             "view_name": "core:manage_tags"},
            {"name": "Can Manage Subgroups", "codename": "core.manage_subgroups",
             "view_name": "core:manage_subgroups"},
            {"name": "Can Manage Environments", "codename": "core.manage_environment",
             "view_name": "core:manage_environment"},
            {"name": "Can Manage Groups", "codename": "core.manage_groups",
             "view_name": "core:manage_groups"},
        ]

        for fp in field_permissions:
            permission, created = Permission.objects.get_or_create(
                codename=fp["codename"],
                defaults={
                    "name": fp["name"],
                    "view_name": fp["view_name"]
                }
            )
            if created:
                created_count += 1
                logger.info(f"Created Field Permission: {fp['name']}")
            else:
                if permission.view_name != fp["view_name"] or permission.name != fp["name"]:
                    logger.warning(f"Field Permission '{fp['name']}' exists with different attributes. Existing: (name='{permission.name}', view_name='{permission.view_name}'), New: (name='{fp['name']}', view_name='{fp['view_name']}'). Skipping update.")
                else:
                    logger.debug(f"Field Permission already exists: {fp['name']}")
            all_permissions.append(permission)

        self.stdout.write(self.style.SUCCESS(f"Successfully created {created_count} Permissions."))

        with transaction.atomic():
            self.create_standard_roles(all_permissions)
            self.assign_roles_to_admin()

    def create_standard_roles(self, permissions):
        standard_roles = {
            "Super Administrator": {
                "description": "Superadmin Role with all permissions.",
                "permissions": permissions
            },
            "Services Editor": {
                "description": "Editor Role with specific field permissions.",
                "permissions": Permission.objects.filter(codename__in=[
                    "can_edit_description",
                    "can_edit_repository",
                    "can_edit_port",
                    "can_edit_version"
                ])
            },
            "Services Administrator": {
                "description": "Editor Role with specific field permissions.",
                "permissions": Permission.objects.filter(codename__in=[
                    "can_edit_description",
                    "can_edit_tags",
                    "can_edit_repository",
                    "can_edit_port",
                    "can_edit_version",
                    "edit_servicebutton_url",
                    "edit_servicebutton_icon",
                    "edit_servicebutton_groups",
                    "edit_servicebutton_connections",
                    "edit_servicebutton_executive",
                    "edit_servicebutton_custom_icon",
                    "edit_servicebutton_dev_language"
                ])
            },
            "User Editor": {
                "description": "Editor Role with specific field permissions.",
                "permissions": Permission.objects.filter(codename__in=[
                    "edit_users",
                    "edit_users_permissions",
                    "edit_users_roles"
                ])
            },
            "Viewer": {
                "description": "Editor Role with specific field permissions.",
                "permissions": Permission.objects.filter(codename__in=[
                    "viewer"
                ])
            },
            "Editor": {
                "description": "Editor Role with specific field permissions.",
                "permissions": Permission.objects.filter(codename__in=[
                    "editor"
                ])
            },
            "Dashboard Viewer": {
                "description": "Editor Role with specific field permissions.",
                "permissions": Permission.objects.filter(codename__in=[
                    "core__devops_dashboard"
                ])
            },
            "Tag Manager": {
                "description": "Editor Role with specific field permissions.",
                "permissions": Permission.objects.filter(codename__in=[
                    "core.manage_tags"
                ])
            },
            "Subgroup Manager": {
                "description": "Editor Role with specific field permissions.",
                "permissions": Permission.objects.filter(codename__in=[
                    "core.manage_subgroups"
                ])
            },
            "Environment Manager": {
                "description": "Editor Role with specific field permissions.",
                "permissions": Permission.objects.filter(codename__in=[
                    "core.manage_environment"
                ])
            },
            "Group Manager": {
                "description": "Editor Role with specific field permissions.",
                "permissions": Permission.objects.filter(codename__in=[
                    "core.manage_groups"
                ])
            },
        }

        for role_name, role_info in standard_roles.items():
            role, created = Role.objects.get_or_create(
                name=role_name,
                defaults={
                    'description': role_info.get('description', '')
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Role '{role_name}' created."))
                logger.info(f"Created Role '{role_name}'.")
            else:
                self.stdout.write(self.style.WARNING(f"Role '{role_name}' already exists. Skipping."))
                logger.debug(f"Role '{role_name}' already exists. Skipping.")

            existing_permissions = set(role.permissions.all())
            new_permissions = [perm for perm in role_info['permissions'] if perm not in existing_permissions]
            if new_permissions:
                role.permissions.add(*new_permissions)
                role.save()
                self.stdout.write(self.style.SUCCESS(f"Added {len(new_permissions)} Permissions to Role '{role_name}'."))
                logger.info(f"Added {len(new_permissions)} Permissions to role '{role_name}'.")
            else:
                self.stdout.write(self.style.WARNING(f"Role '{role_name}' already contains all Permissions."))
                logger.debug(f"Role '{role_name}' already contains all Permissions.")

    def assign_roles_to_admin(self):
        User = get_user_model()
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("Superuser 'admin' not found. Create it with 'createsuperuser' command."))
            logger.error("Superuser 'admin' not found.")
            return

        role_name = "Super Administrator"
        try:
            admin_role = Role.objects.get(name=role_name)
        except Role.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Role '{role_name}' not found. Create it with 'create_roles' command."))
            logger.error(f"Role '{role_name}' not found.")
            return

        if admin_role in admin_user.roles.all():
            self.stdout.write(self.style.WARNING(f"Superuser 'admin' already assigned to role '{role_name}'."))
            logger.debug(f"Superuser 'admin' already assigned to role '{role_name}'.")
        else:
            admin_user.roles.add(admin_role)
            admin_user.save()
            self.stdout.write(self.style.SUCCESS(f"Role '{role_name}' assigned to superuser 'admin'."))
            logger.info(f"Role '{role_name}' assigned to superuser 'admin'.")

    def get_all_view_names(self, resolver, prefix=''):
        view_names = []
        for pattern in resolver.url_patterns:
            if isinstance(pattern, URLPattern):
                if pattern.name:
                    full_view_name = f"{prefix}:{pattern.name}" if prefix else pattern.name
                    view_names.append(full_view_name)
            elif isinstance(pattern, URLResolver):
                sub_prefix = f"{prefix}:{pattern.namespace}" if prefix and pattern.namespace else pattern.namespace or prefix
                view_names += self.get_all_view_names(pattern, prefix=sub_prefix)
        return view_names
