from django.core.management.base import BaseCommand
from devopspanel.core.models import Tag

DEFAULT_TAGS = [
    'Python',
    'DotNet',
    'Queue',
    'Cache',
    'Backend',
    'Frontend',
    'Database',
    'Legacy',
    'DevOps',
    'Security',
    'Testing',
    'GCP',
    'GKE',
    'Erlang',
    'Elixir',
    'Platform',
    'Mobile',
    'Python',
    'Queue',
    'DotNet',
]

class Command(BaseCommand):
    help = 'Seed the database with default tags'

    def handle(self, *args, **options):
        for tag_name in DEFAULT_TAGS:
            tag, created = Tag.objects.get_or_create(name=tag_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Tag "{tag_name}" created.'))
            else:
                self.stdout.write(f'Tag "{tag_name}" already exists.')