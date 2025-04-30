from django.conf import settings
from devopspanel.core.models import Environment, ServiceGroup
import os

def settings_context(_request):
    return {"DEBUG": settings.DEBUG}

def environments_processor(request):

    if not request.user.is_authenticated:
        return {
            'environments': Environment.objects.none(),
            'current_environment': None,
            'groups': ServiceGroup.objects.none(),
            'group_ids': [],
            'tag_names': [],
        }

    if request.user.is_staff:
        environments = Environment.objects.all()
    else:
        environments = request.user.environments.all()

    environment_id = request.GET.get('environment')

    if not environment_id and request.user.current_environment_id:
        environment_id = str(request.user.current_environment_id)

    try:
        current_environment = environments.get(id=environment_id)
    except (Environment.DoesNotExist, ValueError, TypeError):
        current_environment = environments.first()

    if current_environment:
        groups = ServiceGroup.objects.filter(environment=current_environment)
    else:
        groups = ServiceGroup.objects.none()

    group_ids = request.GET.getlist('group')
    tag_names = request.GET.getlist('tag')

    return {
        'environments': environments,
        'current_environment': current_environment,
        'groups': groups,
        'group_ids': group_ids,
        'tag_names': tag_names,
    }

def app_version_processor(request):
    return {
        'app_version': os.getenv('APP_TAG', '1.0.0')  # Default if not set
    }