from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from devopspanel.core.models import ServiceButton, Environment, ServiceGroup, Tag
import logging

logger = logging.getLogger(__name__)

DEFAULT_SERVICE_BUTTONS = [
    {
        'name': 'MyService 1',
        'description': 'Description for MyService 1',
        'url': 'https://myservice1.example.com',
        'environment': 'Production',
        'groups': ['TestGroup'],
        'tags': ['Python', 'Queue'],
        'location': 'K8S',
        'dev_language': 'Python'
    },
    {
        'name': 'MyService 2',
        'description': 'Another service, in staging.',
        'url': 'https://myservice2.example.com',
        'environment': 'Staging',
        'groups': ['TestGroup'],
        'tags': ['DotNet'],
        'location': 'VM-GCP',
        'dev_language': 'C#'
    },
]


class Command(BaseCommand):
    help = 'Seeds the database with default ServiceButtons in existing Environments, Groups, and Tags.'

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("Superuser 'admin' not found. Invoke 'create_users' command first or create an admin.")
            )
            logger.error("Superuser 'admin' not found. Cannot proceed.")
            return

        created_count = 0
        skipped_count = 0

        for button_data in DEFAULT_SERVICE_BUTTONS:
            env_name = button_data.get('environment')
            try:
                env = Environment.objects.get(name=env_name)
            except Environment.DoesNotExist:
                self.stdout.write(self.style.WARNING(
                    f"Environment '{env_name}' not found. Skipping creation of '{button_data['name']}'."
                ))
                continue

            defaults = {
                'description': button_data.get('description', ''),
                'url': button_data.get('url', ''),
                'created_by': admin_user,
                'location': button_data.get('location', 'VM-GCP'),
                'dev_language': button_data.get('dev_language', ''),
            }

            sb_obj, created = ServiceButton.objects.get_or_create(
                name=button_data['name'],
                environment=env,
                defaults=defaults,
            )

            if created:
                groups_list = button_data.get('groups', [])
                for group_name in groups_list:
                    group_qs = ServiceGroup.objects.filter(name=group_name, environment=env)
                    if group_qs.exists():
                        group = group_qs.first()
                        sb_obj.groups.add(group)
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"Group '{group_name}' not found in environment '{env_name}'."
                        ))

                tags_list = button_data.get('tags', [])
                for tag_name in tags_list:
                    try:
                        tag_obj = Tag.objects.get(name=tag_name)
                        sb_obj.tags.add(tag_obj)
                    except Tag.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f"Tag '{tag_name}' not found."))

                sb_obj.save()
                created_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"ServiceButton '{sb_obj.name}' created in '{env_name}' environment."
                ))
            else:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(
                    f"ServiceButton '{sb_obj.name}' already exists in '{env_name}' environment. Skipping."
                ))

        self.stdout.write(self.style.SUCCESS(
            f"Seeding complete. Created: {created_count}, Skipped: {skipped_count}."
        ))
