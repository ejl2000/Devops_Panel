# dashboard/views.py

from django.views.generic import TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from devopspanel.core.models import Environment, ServiceGroup, ServiceButton, CodeBase
from django.http import JsonResponse
from django.db.models import Count
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)

User = get_user_model()

def is_admin(user):
    return user.is_staff

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/main.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        environments = user.environments.all()
        env_id = self.request.GET.get('environment')

        logger.info(f"User '{user.username}' accessing DashboardView.")
        logger.info(f"Available Environments: {[env.name for env in environments]}")

        if env_id:
            try:
                current_environment = Environment.objects.get(id=env_id, users=user)
                if user.current_environment != current_environment:
                    user.current_environment = current_environment
                    user.save()
                logger.info(f"Environment set via GET: {current_environment.name} (ID: {current_environment.id})")
            except Environment.DoesNotExist:
                logger.error(f"Environment with ID {env_id} does not exist or user lacks access.")
                messages.error(request, 'Environment not exist or you don`t have access to it.')
                return redirect('core:dashboard')
        elif user.current_environment and environments.filter(id=user.current_environment.id).exists():
            current_environment = user.current_environment
            logger.info(
                f"Environment set via user.current_environment: {current_environment.name} (ID: {current_environment.id})")
        else:
            current_environment = environments.first() if environments.exists() else None
            if current_environment:
                user.current_environment = current_environment
                user.save()
                logger.info(
                    f"Environment set to first available: {current_environment.name} (ID: {current_environment.id})")
            else:
                logger.warning("No available environments for the user.")

        if not current_environment:
            context['servicebuttons_per_group'] = []
            context['total_users'] = 0
            context['codebases_per_servicebutton'] = []
            context['environments'] = environments
            context['current_environment'] = None
            return context

        context['environments'] = environments
        context['current_environment'] = current_environment

        context['servicebuttons_per_group'] = list(
            ServiceGroup.objects.filter(environment=current_environment)
            .annotate(button_count=Count('buttons'))
            .values('name', 'button_count')
        )

        context['total_users'] = User.objects.count()

        codebase_exists_count = ServiceButton.objects.filter(
            environment=current_environment,
            code_base__isnull=False
        ).count()
        codebase_missing_count = ServiceButton.objects.filter(
            environment=current_environment,
            code_base__isnull=True
        ).count()

        context['codebase_exists'] = codebase_exists_count
        context['codebase_missing'] = codebase_missing_count

        context['servicebuttons_per_location'] = list(
            ServiceButton.objects.filter(environment=current_environment)
            .values('location')
            .annotate(count=Count('id'))  # или Count('*')
            .order_by('location')
        )

        context['codebases_per_servicebutton'] = list(
            ServiceButton.objects.filter(environment=current_environment)
            .annotate(codebase_count=Count('code_base'))
            .values('name', 'codebase_count')
        )

        logger.info(f"Context data for environment '{current_environment.name}':")
        logger.info(f"ServiceButtons per Group: {context['servicebuttons_per_group']}")
        logger.info(f"Total Users: {context['total_users']}")
        logger.info(f"CodeBases per ServiceButton: {context['codebases_per_servicebutton']}")

        return context

class FetchDashboardDataView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        user = request.user
        env_id = request.GET.get('environment')

        if env_id:
            try:
                current_environment = Environment.objects.get(id=env_id, users=user)
            except Environment.DoesNotExist:
                return JsonResponse({'error': 'Environment does not exist or you do not have access'}, status=404)
        else:
            current_environment = user.environments.first()

        if not current_environment:
            return JsonResponse({'error': 'No Environment selected or available'}, status=400)

        servicebuttons_per_group = list(
            ServiceGroup.objects.filter(environment=current_environment)
            .annotate(button_count=Count('buttons'))
            .values('name', 'button_count')
        )

        total_users = current_environment.users.count()

        codebases_per_servicebutton = list(
            ServiceButton.objects.filter(environment=current_environment)
            .annotate(codebase_count=Count('code_base'))
            .values('name', 'codebase_count')
        )

        data = {
            'servicebuttons_per_group': servicebuttons_per_group,
            'total_users': total_users,
            'codebases_per_servicebutton': codebases_per_servicebutton,
        }

        return JsonResponse(data)

index_view = DashboardView.as_view(template_name="dashboard/main.html")