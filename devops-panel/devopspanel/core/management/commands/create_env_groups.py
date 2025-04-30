from django.core.management.base import BaseCommand
from devopspanel.core.models import Environment, ServiceGroup
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Creating standard environments and groups for each environment, avoiding duplications.'

    def handle(self, *args, **options):
        User = get_user_model()

        environments = ['Production', 'Staging']
        standard_groups = ['Receivers', 'Common Services', 'Micro-Services', 'Platform', 'Ops-Services', 'TestGroup']

        try:
            creator = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR("Superuser 'admin' not found. invoke 'create_users' command first."))
            logger.error("Superuser 'admin' not found. invoke 'create_users' command first.")
            return

        env_created_count = 0
        group_created_count = 0

        for env_name in environments:
            environment, env_created = Environment.objects.get_or_create(
                name=env_name,
                defaults={'created_by': creator}
            )
            if env_created:
                env_created_count += 1
                self.stdout.write(self.style.SUCCESS(f"Environment '{env_name}' created."))
                logger.info(f"Created environment '{env_name}'.")
            else:
                self.stdout.write(self.style.WARNING(f"Environment '{env_name}' already exist. Skipping creation."))
                logger.debug(f"Environment '{env_name}' already exist. Skipping creation.")

            for group_name in standard_groups:
                group, group_created = ServiceGroup.objects.get_or_create(
                    name=group_name,
                    environment=environment,
                    defaults={'created_by': creator}
                )
                if group_created:
                    group_created_count += 1
                    self.stdout.write(self.style.SUCCESS(f"Group '{group_name}' for environment '{env_name}' created."))
                    logger.info(f"Created group '{group_name}' for environment '{env_name}'.")
                else:
                    self.stdout.write(self.style.WARNING(f"Group '{group_name}' for environment '{env_name}' already exists. Skipping."))
                    logger.debug(f"Group '{group_name}' for environment '{env_name}' already exists. Skipping.")

        self.stdout.write(self.style.SUCCESS(
            f"Successfully created {env_created_count} environments and {group_created_count} groups."
        ))