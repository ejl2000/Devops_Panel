import string
import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Creating superuser with random password and test user with simple random password.'

    def handle(self, *args, **options):
        User = get_user_model()

        super_username = 'admin'
        super_email = 'admin@admin.com'
        if User.objects.filter(username=super_username).exists():
            self.stdout.write(self.style.WARNING(f"Superuser with username '{super_username}' already exists. Skipping."))
        else:
            super_password = self.generate_random_password()
            User.objects.create_superuser(
                username=super_username,
                email=super_email,
                password=super_password
            )
            self.stdout.write(self.style.SUCCESS(f"Superuser '{super_username}' Created. Passowrd: {super_password}"))
            logger.info(f"Created superuser '{super_username}' with password '{super_password}'.")

        test_username = 'testuser'
        test_email = 'testuser@example.com'
        test_password = 'testpassword'
        if User.objects.filter(username=test_username).exists():
            self.stdout.write(self.style.WARNING(f"Test user with username '{test_username}' already exists. Skipping."))
        else:
            User.objects.create_user(
                username=test_username,
                email=test_email,
                password=test_password
            )
            self.stdout.write(self.style.SUCCESS(f"Test user '{test_username}' created with passwod: '{test_password}'."))
            logger.info(f"Created test user '{test_username}' with password '{test_password}'.")

    def generate_random_password(self, length=12):
        characters = string.ascii_letters + string.digits + string.punctuation
        characters = characters.replace('"', '').replace("'", '').replace('\\', '')
        password = ''.join(random.choice(characters) for _ in range(length))
        return password