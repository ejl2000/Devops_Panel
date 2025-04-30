from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from devopspanel.core.models import ServiceButton, ServiceGroup, Environment, ServiceButtonLink, CodeBase, CodeBaseDependency, BearerToken, SubGroup, Tag, Maintenance
from devopspanel.users.models import Role, Permission
from devopspanel.dashboard.forms import (
    ServiceButtonForm,
    ServiceButtonLinkFormSet,
    GroupForm,
    EnvironmentForm,
    ICON_CHOICES,
    CodeBaseDependencyFormSetCreate,
    CodeBaseDependencyFormSetEdit,
    SubGroupForm,
    TagForm,
    APIKeyCreateForm,
    MaintenanceForm
)
import pprint
from django.urls import reverse
import logging
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth import authenticate
from datetime import timedelta
import uuid
from django.views.decorators.http import require_POST, require_GET
import json
from devopspanel.utils.api_utils import bearer_token_required
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.loader import render_to_string
from .decorators import any_permission_required
from django.db.models import Exists, OuterRef

logger = logging.getLogger(__name__)

User = get_user_model()

def is_admin(user):
    return user.is_staff

# Dashboard View
@login_required
def dashboard_view(request, environment_id=None):
    if request.user.is_staff:
        user_environments = Environment.objects.all()
    else:
        user_environments = request.user.environments.all()

    environment_id = request.GET.get('environment') if not environment_id else environment_id

    current_environment = request.user.current_environment
    if not current_environment:
        current_environment = user_environments.first()
        request.user.current_environment = current_environment
        request.user.save()

    if not request.user.is_staff and request.user not in current_environment.users.all():
        messages.error(request, "You don't have permissions for that Environment.")
        return redirect('core:dashboard')

    groups = ServiceGroup.objects.filter(environment=current_environment)
    subgroups = SubGroup.objects.filter(group__in=groups)
    buttons = ServiceButton.objects.filter(environment=current_environment)

    group_ids = request.GET.getlist('group')
    tag_names = request.GET.getlist('tag')
    subgroup_ids = request.GET.getlist('subgroup')
    location_filters = request.GET.getlist('location')
    search_query = request.GET.get('search', '').strip()
    is_search = bool(search_query)

    if group_ids:
        buttons = buttons.filter(groups__id__in=group_ids)
    if tag_names:
        buttons = buttons.filter(tags__name__in=tag_names)
    if subgroup_ids:
        buttons = buttons.filter(subgroup__id__in=subgroup_ids)
    if location_filters:
        buttons = buttons.filter(location__in=location_filters)
    if search_query:
        buttons = buttons.filter(
            Q(name__icontains=search_query) |
            Q(tags__name__icontains=search_query) |
            Q(ip__icontains=search_query) |
            Q(dev_language__icontains=search_query) |
            Q(location__icontains=search_query)
        ).distinct()

    now = timezone.now()
    soon_threshold = now + timedelta(hours=3)

    maintenances_soon_subquery = Maintenance.objects.filter(
        service_buttons=OuterRef('pk'),
        start_time__gte=now,
        start_time__lte=soon_threshold,
        status='scheduled'
    )

    maintenances_in_subquery = Maintenance.objects.filter(
        service_buttons=OuterRef('pk'),
        start_time__lte=now,
        end_time__gte=now,
        status='in_progress'
    )

    buttons = buttons.annotate(
        has_maintenance_soon=Exists(maintenances_soon_subquery),
        has_in_maintenance=Exists(maintenances_in_subquery)
    ).prefetch_related(
        'code_base__dependencies__dependencies',
        'tags',
        'groups',
        'subgroup'
    ).distinct()

    for button in buttons:
        logger.debug(
            f"Button '{button.name}' - has_maintenance_soon: {button.has_maintenance_soon}, has_in_maintenance: {button.has_in_maintenance}"
        )

    total_users = User.objects.count()
    total_groups = ServiceGroup.objects.count()
    total_buttons = ServiceButton.objects.count()
    total_environments = Environment.objects.count()

    tags = buttons.values_list('tags__name', flat=True).distinct()

    grouped_buttons = {}
    for button in buttons:
        for g in button.groups.all():
            if g.id not in grouped_buttons:
                grouped_buttons[g.id] = {
                    'group': g,
                    'subgroups': {}
                }
            subgroup_name = button.subgroup.name if button.subgroup else 'No SubGroup'
            if subgroup_name not in grouped_buttons[g.id]['subgroups']:
                grouped_buttons[g.id]['subgroups'][subgroup_name] = []
            grouped_buttons[g.id]['subgroups'][subgroup_name].append(button)
            logger.debug(f"Button '{button.name}' added to group '{g.name}' under subgroup '{subgroup_name}'")

    group_ids_json = json.dumps(group_ids)
    tag_names_json = json.dumps(tag_names)

    DEV_LANGUAGE_ICONS = {
        'Python': 'icons/python.svg',
        'Java': 'icons/java.svg',
        'C++': 'icons/cplusplus.svg',
        'C#': 'icons/csharp.svg',
        'JavaScript': 'icons/javascript.svg',
        'Ruby': 'icons/ruby.svg',
        'PHP': 'icons/php.svg',
        'Go': 'icons/go.svg',
        'Swift': 'icons/swift.svg',
        'Kotlin': 'icons/kotlin.svg',
        'Perl': 'icons/perl.svg',
        'Rust': 'icons/rust.svg',
        'Scala': 'icons/scala.svg',
        'Objective-C': 'icons/objectivec.svg',
        'Dart': 'icons/dart.svg',
        'TypeScript': 'icons/typescript.svg',
        'Elixir': 'icons/elixir.svg',
        'Haskell': 'icons/haskell.svg',
        'Lua': 'icons/lua.svg',
        'Erlang': 'icons/erlang.svg',
        'Matlab': 'icons/matlab.svg',
        'SQL': 'icons/sql.svg',
        'PL/SQL': 'icons/plsql.svg',
        'T-SQL': 'icons/tsql.svg',
        'MySQL': 'icons/mysql.svg',
        'PostgreSQL': 'icons/postgresql.svg',
        'MongoDB': 'icons/mongodb.svg',
        'SQLite': 'icons/sqlite.svg',
        'Redis': 'icons/redis.svg',
        'Cassandra': 'icons/cassandra.svg',
        'MariaDB': 'icons/mariadb.svg',
        'Oracle': 'icons/oracle.svg',
    }

    LOCATION_ICONS = {
        'K8S': 'icons/kubernetes.svg',
        'VM-GCP': 'icons/google_cloud.svg',
        'Cloud-SQL': 'icons/google_cloud_sql.svg',
        'CloudFlare': 'icons/cloudflare.svg',
        'AWS': 'icons/aws.svg',
        'Bare-Metal': 'icons/bare_metal.svg',
    }

    environments = user_environments

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        rendered_buttons = render_to_string('dashboard/button_container.html', {
            'grouped_buttons': grouped_buttons,
            'location_icons': LOCATION_ICONS,
            'dev_language_icons': DEV_LANGUAGE_ICONS,
            'user': request.user,
            'is_search': is_search,
        }, request=request)
        return JsonResponse({'html': rendered_buttons, 'is_search': is_search})

    logger.info(f"Current Time: {now}")
    logger.info(f"Soon Threshold: {soon_threshold}")
    logger.info(f"Buttons Count: {buttons.count()}")
    logger.info("Grouped Buttons Structure:")
    logger.info(pprint.pformat(grouped_buttons))

    return render(request, 'dashboard/index.html', {
        'current_environment': current_environment,
        'groups': groups,
        'group_ids': group_ids,
        'tag_names': tag_names,
        'subgroup_ids': subgroup_ids,
        'location_filters': location_filters,
        'search_query': search_query,
        'tags': tags,
        'total_users': total_users,
        'total_groups': total_groups,
        'total_buttons': total_buttons,
        'total_environments': total_environments,
        'grouped_buttons': grouped_buttons,
        'group_ids_json': group_ids_json,
        'tag_names_json': tag_names_json,
        'environments': environments,
        'location_icons': LOCATION_ICONS,
        'dev_language_icons': DEV_LANGUAGE_ICONS,
        'subgroups': subgroups,
        'is_search': is_search,
    })

@any_permission_required([
    'core.add_button',
])
def add_button(request, environment_id=None):
    if 'environment' in request.GET:
        environment_id = request.GET.get('environment')
    if environment_id:
        current_environment = get_object_or_404(Environment, id=environment_id)
    else:
        current_environment = None

    if request.method == 'POST':
        form = ServiceButtonForm(request.POST, request.FILES, user=request.user)
        formset = ServiceButtonLinkFormSet(request.POST, request.FILES, instance=ServiceButton(), prefix='links')
        codebase_dependency_formset = CodeBaseDependencyFormSetCreate(request.POST, request.FILES, instance=CodeBase(), prefix='dependencies')

        if form.is_valid():
            selected_groups = form.cleaned_data.get('groups')
        else:
            selected_groups_ids = request.POST.getlist('groups')
            selected_groups = ServiceGroup.objects.filter(id__in=selected_groups_ids)
            logger.error(f"Form errors: {form.errors}")
            logger.error(f"Formset errors: {formset.errors}")
            logger.error(f"Subgroup Formset errors: {codebase_dependency_formset.errors}")

        if current_environment:
            subgroups = SubGroup.objects.filter(group__in=selected_groups, group__environment=current_environment)
        else:
            subgroups = SubGroup.objects.filter(group__in=selected_groups)

        subgroups_data = {}
        for subgroup in subgroups:
            group_id = subgroup.group.id
            if group_id not in subgroups_data:
                subgroups_data[group_id] = []
            subgroups_data[group_id].append({'id': subgroup.id, 'name': subgroup.name})

        if form.is_valid() and formset.is_valid() and codebase_dependency_formset.is_valid():
            button = form.save(commit=False)
            button.created_by = request.user
            button.environment = current_environment or form.cleaned_data['environment']
            button.save()
            form.save_m2m()
            formset.instance = button
            if form.cleaned_data.get('is_multi_link'):
                formset.save()
            else:
                button.links.all().delete()
            if form.cleaned_data.get('has_code_base'):
                code_base = button.code_base
                codebase_dependency_formset.instance = code_base
                if form.cleaned_data.get('has_code_base_dependencies'):
                    codebase_dependency_formset.save()
                else:
                    code_base.dependencies.all().delete()
            messages.success(request, 'Button created successfully!')
            dashboard_url = reverse('dashboard:index')
            if button.environment:
                return redirect(f"{dashboard_url}?environment={button.environment.id}")
            else:
                return redirect('dashboard:index')
        else:
            messages.error(request, 'Please check errors in the form.')
    else:
        form = ServiceButtonForm(user=request.user)
        formset = ServiceButtonLinkFormSet(instance=ServiceButton(), prefix='links')
        codebase_dependency_formset = CodeBaseDependencyFormSetCreate(instance=CodeBase(), prefix='dependencies')
        if current_environment:
            form.fields['environment'].initial = current_environment
            form.fields['groups'].queryset = ServiceGroup.objects.filter(environment=current_environment)
            subgroups = SubGroup.objects.filter(group__environment=current_environment)
        else:
            subgroups = SubGroup.objects.all()
        subgroups_data = {}
        for subgroup in subgroups:
            group_id = subgroup.group.id
            if group_id not in subgroups_data:
                subgroups_data[group_id] = []
            subgroups_data[group_id].append({'id': subgroup.id, 'name': subgroup.name})

    return render(request, 'core/add_service_button.html', {
        'form': form,
        'formset': formset,
        'codebase_dependency_formset': codebase_dependency_formset,
        'current_environment': current_environment,
        'ICON_CHOICES': json.dumps([choice[0] for choice in ICON_CHOICES]),
        'subgroups_data': json.dumps(subgroups_data),
    })

@login_required
@any_permission_required([
    'core.*',
    'core.edit_button',
    'core.edit_servicebutton_repository',
    'core.edit_servicebutton_description',
    'core.edit_servicebutton_version',
    'core.edit_servicebutton_tags',
    'core.edit_servicebutton_port',
])
def edit_button(request, button_id):
    button = get_object_or_404(ServiceButton, id=button_id)
    current_environment = button.environment

    tab_fields = {
        'step1': [
            'name', 'description', 'is_multi_link', 'url', 'links',
            'icon_choice', 'custom_icon', 'tags'
        ],
        'step2': ['groups', 'subgroup', 'environment'],
        'step3': [
            'connections', 'executive', 'dev_language', 'ip', 'port',
            'version', 'location'
        ],
        'step4': [
            'has_code_base', 'code_base_name', 'code_base_url', 'has_code_base_dependencies'
        ],
        'step5': [],
    }

    if request.method == 'POST':
        form = ServiceButtonForm(
            data=request.POST,
            files=request.FILES,
            instance=button,
            user=request.user
        )
        formset = ServiceButtonLinkFormSet(
            data=request.POST,
            files=request.FILES,
            instance=button,
            prefix='links'
        )
        codebase_dependency_formset = CodeBaseDependencyFormSetEdit(
            data=request.POST,
            files=request.FILES,
            instance=button.code_base or CodeBase(),
            prefix='dependencies'
        )

        if form.is_valid() and formset.is_valid() and codebase_dependency_formset.is_valid():
            # Сохранение данных
            button = form.save()
            form.save_m2m()

            formset.instance = button
            if form.cleaned_data.get('is_multi_link'):
                formset.save()
            else:
                button.links.all().delete()

            if form.cleaned_data.get('has_code_base'):
                code_base = button.code_base
                if form.cleaned_data.get('has_code_base_dependencies'):
                    codebase_dependency_formset.instance = code_base
                    codebase_dependency_formset.save()
                else:
                    code_base.dependencies.all().delete()
            else:
                if button.code_base:
                    button.code_base.dependencies.all().delete()
                    button.code_base.delete()
                    button.code_base = None

            messages.success(request, 'Button edited successfully!')
            dashboard_url = reverse('core:devops_dashboard')
            if button.environment:
                return redirect(f"{dashboard_url}?environment={button.environment.id}")
            else:
                return redirect('core:devops_dashboard')
        else:
            # Определяем первый шаг с ошибками
            currentStep = 1  # По умолчанию первый шаг
            for step, fields in tab_fields.items():
                step_number = int(step.replace('step', ''))
                has_error = False
                for field in fields:
                    if field in form.errors:
                        currentStep = step_number
                        has_error = True
                        break
                    # Проверяем ошибки в formset
                    for form_error in formset.errors:
                        if field in form_error:
                            currentStep = step_number
                            has_error = True
                            break
                    if has_error:
                        break
                if has_error:
                    break

            # Аналогично проверяем ошибки в codebase_dependency_formset
            for form_error in codebase_dependency_formset.errors:
                if any(field in form_error for field in tab_fields['step4']):
                    currentStep = 4
                    break

            # Определение видимости табов
            tab_visibility = {
                'step1': True,  # Всегда показываем вкладку "Basic Information"
                'step2': any(field in form.fields for field in tab_fields['step2']),
                'step3': any(field in form.fields for field in tab_fields['step3']),
                'step4': any(field in form.fields for field in tab_fields['step4']),
                'step5': True,  # Всегда показываем вкладку "Confirmation"
            }

            # Подготовка данных для шаблона
            if form.is_valid():
                selected_groups = form.cleaned_data.get('groups')
            else:
                selected_groups_ids = request.POST.getlist('groups')
                selected_groups = ServiceGroup.objects.filter(id__in=selected_groups_ids)
                logger.error(f"Form errors: {form.errors}")
                logger.error(f"Formset errors: {formset.errors}")
                logger.error(f"Codebase Dependency Formset errors: {codebase_dependency_formset.errors}")

            if current_environment:
                subgroups = SubGroup.objects.filter(group__in=selected_groups, group__environment=current_environment)
            else:
                subgroups = SubGroup.objects.filter(group__in=selected_groups)

            subgroups_data = {}
            for subgroup in subgroups:
                group_id = subgroup.group.id
                if group_id not in subgroups_data:
                    subgroups_data[group_id] = []
                subgroups_data[group_id].append({'id': subgroup.id, 'name': subgroup.name})

            current_subgroup_id = button.subgroup.id if button.subgroup else None

    else:
        # Обработка GET-запроса
        form = ServiceButtonForm(instance=button, user=request.user)
        formset = ServiceButtonLinkFormSet(instance=button, prefix='links')
        codebase_dependency_formset = CodeBaseDependencyFormSetEdit(
            instance=button.code_base or CodeBase(),
            prefix='dependencies'
        )

        # Определение видимости табов
        tab_visibility = {
            'step1': True,  # Всегда показываем вкладку "Basic Information"
            'step2': any(field in form.fields for field in tab_fields['step2']),
            'step3': any(field in form.fields for field in tab_fields['step3']),
            'step4': any(field in form.fields for field in tab_fields['step4']),
            'step5': True,  # Всегда показываем вкладку "Confirmation"
        }

        subgroups = SubGroup.objects.filter(
            group__in=ServiceGroup.objects.filter(environment=current_environment)
        )
        subgroups_data = {}
        for subgroup in subgroups:
            group_id = subgroup.group.id
            if group_id not in subgroups_data:
                subgroups_data[group_id] = []
            subgroups_data[group_id].append({'id': subgroup.id, 'name': subgroup.name})

        current_subgroup_id = button.subgroup.id if button.subgroup else None
        currentStep = 1  # Первый шаг при GET-запросе

    return render(
        request,
        'core/edit_service_button.html',
        {
            'form': form,
            'formset': formset,
            'codebase_dependency_formset': codebase_dependency_formset,
            'button': button,
            'current_environment': current_environment,
            'subgroups_data': json.dumps(subgroups_data),
            'current_subgroup_id': current_subgroup_id,
            'tab_visibility': tab_visibility,
            'currentStep': currentStep,
        }
    )

# Delete Button View
@user_passes_test(is_admin)
def delete_button(request, button_id):
    button = get_object_or_404(ServiceButton, id=button_id)
    current_environment = button.environment
    if request.user != button.created_by and not request.user.is_staff:
        messages.error(request, "You don't have permissions to delete that Service Button.")
        return redirect('dashboard:index')
    if request.method == 'POST':
        button.delete()
        messages.success(request, 'Button deleted successfully!')
        dashboard_url = reverse('dashboard:index')
        if current_environment:
            return redirect(f"{dashboard_url}?environment={current_environment.id}")
        else:
            return redirect('dashboard:index')
    return render(request, 'core/confirm_delete.html', {
        'button': button,
        'current_environment': current_environment,
    })

# Group List View
@any_permission_required(['core.manage_groups'])
def group_list(request):
    groups = ServiceGroup.objects.all()
    return render(request, 'core/group_list.html', {'groups': groups})

# Add Group View
@any_permission_required(['core.manage_groups'])
def add_group(request):
    if 'environment' in request.GET:
        environment_id = request.GET.get('environment')
    else:
        environment_id = None
    if environment_id:
        current_environment = get_object_or_404(Environment, id=environment_id)
    else:
        current_environment = None
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.environment = current_environment or form.cleaned_data['environment']
            group.save()
            messages.success(request, 'Group successfully created!')
            return redirect('core:group_list')
        else:
            messages.error(request, 'Please re-check errors in the form.')
    else:
        form = GroupForm()
        if current_environment:
            form.fields['environment'].initial = current_environment
    return render(request, 'core/add_group.html', {
        'form': form,
        'current_environment': current_environment,
    })

# Edit Group View
@any_permission_required(['core.manage_groups'])
def edit_group(request, group_id):
    group = get_object_or_404(ServiceGroup, id=group_id)
    current_environment = group.environment
    if request.user != group.created_by and not request.user.is_staff:
        messages.error(request, "You don't have permissions to edit this group.")
        return redirect('core:group_list')
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, 'Group successfully edited!')
            return redirect('core:group_list')
        else:
            messages.error(request, 'Please re-check errors in the form.')
    else:
        form = GroupForm(instance=group)
    return render(request, 'core/edit_group.html', {
        'form': form,
        'group': group,
        'current_environment': current_environment,
    })

# Delete Group View
@any_permission_required(['core.manage_groups'])
def delete_group(request, group_id):
    group = get_object_or_404(ServiceGroup, id=group_id)
    current_environment = group.environment
    if request.user != group.created_by and not request.user.is_staff:
        messages.error(request, "You don't have permissions to delete this group.")
        return redirect('core:group_list')
    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Group successfully deleted!')
        return redirect('core:group_list')
    return render(request, 'core/confirm_delete_group.html', {
        'group': group,
        'current_environment': current_environment,
    })

# Environment List View
@any_permission_required(['core.manage_environment'])
def environment_list(request):
    environments = Environment.objects.all()
    return render(request, 'core/environment_list.html', {'environments': environments})

# Add Environment View
@any_permission_required(['core.manage_environment'])
def add_environment(request):
    if request.method == 'POST':
        form = EnvironmentForm(request.POST)
        if form.is_valid():
            environment = form.save(commit=False)
            environment.created_by = request.user
            environment.save()
            messages.success(request, 'Environment successfully created!')
            return redirect('core:environment_list')
        else:
            messages.error(request, 'Please re-check errors in the form.')
    else:
        form = EnvironmentForm()
    return render(request, 'core/add_environment.html', {'form': form})

# Edit Environment View
@any_permission_required(['core.manage_environment'])
def edit_environment(request, environment_id):
    environment = get_object_or_404(Environment, id=environment_id)
    if request.method == 'POST':
        form = EnvironmentForm(request.POST, instance=environment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Environment successfully edited!')
            return redirect('core:environment_list')
        else:
            messages.error(request, 'Please re-check errors in the form.')
    else:
        form = EnvironmentForm(instance=environment)
    return render(request, 'core/edit_environment.html', {
        'form': form,
        'environment': environment,
    })

# Delete Environment View
@any_permission_required(['core.manage_environment'])
def delete_environment(request, environment_id):
    environment = get_object_or_404(Environment, id=environment_id)
    if request.method == 'POST':
        environment.delete()
        messages.success(request, 'Environment successfully deleted!')
        return redirect('core:environment_list')
    return render(request, 'core/confirm_delete_environment.html', {'environment': environment})

# Infrastructure Data View
@login_required
@require_GET
def infrastructure_data(request):
    try:
        environment_id = request.GET.get('environment')
        if not environment_id:
            return JsonResponse({'error': 'Environment not specified'}, status=400)

        try:
            environment = Environment.objects.get(id=environment_id)
        except Environment.DoesNotExist:
            return JsonResponse({'error': 'Environment does not exist'}, status=404)

        tag_filters = request.GET.getlist('tag')
        group_filters = request.GET.getlist('group')
        name_filter = request.GET.get('name', '').strip()

        buttons = ServiceButton.objects.filter(environment=environment)
        if group_filters:
            buttons = buttons.filter(groups__id__in=group_filters)
        if tag_filters:
            buttons = buttons.filter(tags__name__in=tag_filters)
        if name_filter:
            buttons = buttons.filter(name__icontains=name_filter)

        buttons = buttons.select_related('subgroup').prefetch_related('connections', 'tags', 'groups')

        elements = []
        group_colors = {}
        subgroup_colors = {}
        color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

        all_groups = ServiceGroup.objects.filter(environment=environment, buttons__in=buttons).distinct()
        all_subgroups = SubGroup.objects.filter(group__in=all_groups, buttons__in=buttons).distinct()

        for idx, group in enumerate(all_groups):
            group_colors[group.id] = color_palette[idx % len(color_palette)]

        for idx, subgroup in enumerate(all_subgroups):
            subgroup_colors[subgroup.id] = color_palette[idx % len(color_palette)]

        for group in all_groups:
            elements.append({
                'data': {
                    'id': f'group_{group.id}',
                    'label': group.name,
                    'color': group_colors[group.id],
                },
                'classes': 'groupNode'
            })

        for sg in all_subgroups:
            elements.append({
                'data': {
                    'id': f'subgroup_{sg.id}',
                    'label': sg.name,
                    'parent': f'group_{sg.group.id}',
                    'color': subgroup_colors[sg.id],
                },
                'classes': 'subgroupNode'
            })

        for button in buttons:
            parent_id = None
            grp = button.groups.first()
            sbg = button.subgroup
            if sbg:
                parent_id = f'subgroup_{sbg.id}'
            elif grp:
                parent_id = f'group_{grp.id}'

            if sbg and sbg.id in subgroup_colors:
                color = subgroup_colors[sbg.id]
            elif grp and grp.id in group_colors:
                color = group_colors[grp.id]
            else:
                color = '#808080'

            elements.append({
                'data': {
                    'id': f'service_{button.id}',
                    'label': button.name,
                    'color': color,
                    'parent': parent_id,
                    'description': button.description or '',
                    'ip': button.ip or '',
                    'port': button.port or '',
                    'version': button.version or '',
                    'location': button.location or '',
                    'dev_language': button.dev_language or '',
                    'executive': button.executive.get_full_name() if button.executive else '',
                    'tags': list(button.tags.values_list('name', flat=True)),
                }
            })

        added_edges = set()
        for b in buttons:
            for c in b.connections.all():
                if c.environment == environment and c in buttons:
                    edge_id = f'link_{b.id}_{c.id}'
                    if edge_id not in added_edges and f'link_{c.id}_{b.id}' not in added_edges:
                        elements.append({
                            'data': {
                                'id': edge_id,
                                'source': f'service_{b.id}',
                                'target': f'service_{c.id}',
                                'color': '#999'
                            }
                        })
                        added_edges.add(edge_id)

        return JsonResponse({'elements': elements})
    except Exception as e:
        logger.exception("Error in infrastructure_data view")
        return JsonResponse({'error': 'Internal server error'}, status=500)

@user_passes_test(is_admin)
def trigger_error(request):
    division_by_zero = 1 / 0  # This will raise a ZeroDivisionError

@csrf_exempt
def obtain_bearer_token(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if not username or not password:
            return JsonResponse({'error': 'Username and password required'}, status=400)
        user = authenticate(request=request, username=username, password=password)
        if user is not None:
            token = str(uuid.uuid4())
            expires_at = timezone.now() + timedelta(hours=24)
            BearerToken.objects.create(token=token, user=user, expires_at=expires_at)
            return JsonResponse({'token': token, 'expires_at': expires_at.isoformat()})
        else:
            return JsonResponse({'error': 'Invalid credentials'}, status=401)
    else:
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)

@require_POST
@csrf_exempt
@bearer_token_required
def update_version(request):
    try:
        data = json.loads(request.body)
        button_name = data.get('name')
        version = data.get('version')
        environment_id = data.get('environment_id')

        if not button_name or not version or not environment_id:
            return JsonResponse({'error': 'Name, version и environment_id required'}, status=400)

        try:
            environment = Environment.objects.get(id=environment_id)
        except Environment.DoesNotExist:
            return JsonResponse({'error': 'Environment not exist'}, status=404)

        try:
            service_button = ServiceButton.objects.get(name=button_name, environment=environment)
            service_button.version = version
            service_button.save()
            return JsonResponse({'message': 'Version Successfully updated.'})
        except ServiceButton.DoesNotExist:
            return JsonResponse({'error': 'ServiceButton with specified name not found in that Environment'}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Wrong JSON Format'}, status=400)

@require_POST
@csrf_exempt
@bearer_token_required
def revoke_token(request):
    token = request.META.get('HTTP_AUTHORIZATION')[7:]
    try:
        bearer_token = BearerToken.objects.get(token=token)
        bearer_token.delete()
        return JsonResponse({'message': 'Token revoked successfully'}, status=200)
    except BearerToken.DoesNotExist:
        return JsonResponse({'error': 'Token not found'}, status=404)

# List Subgroup
@any_permission_required(['core.manage_subgroups'])
def subgroup_list(request):
    subgroups = SubGroup.objects.select_related('group__environment').all()
    return render(request, 'core/subgroup_list.html', {'subgroups': subgroups})

# Add Subgroup
@any_permission_required(['core.manage_subgroups'])
def add_subgroup(request):
    if request.method == 'POST':
        form = SubGroupForm(request.POST)
        if form.is_valid():
            subgroup = form.save(commit=False)
            subgroup.created_by = request.user
            subgroup.save()
            messages.success(request, 'SubGroup successfully created!')
            return redirect('core:subgroup_list')
        else:
            messages.error(request, 'Please check the form for errors.')
    else:
        form = SubGroupForm()
    return render(request, 'core/add_subgroup.html', {'form': form})

# Edit Subgroup
@any_permission_required(['core.manage_subgroups'])
def edit_subgroup(request, subgroup_id):
    subgroup = get_object_or_404(SubGroup, id=subgroup_id)
    if request.method == 'POST':
        form = SubGroupForm(request.POST, instance=subgroup)
        if form.is_valid():
            form.save()
            messages.success(request, 'SubGroup successfully updated!')
            return redirect('core:subgroup_list')
        else:
            messages.error(request, 'Please check the form for errors.')
    else:
        form = SubGroupForm(instance=subgroup)
    return render(request, 'core/edit_subgroup.html', {'form': form, 'subgroup': subgroup})

# Remove Subgroup
@any_permission_required(['core.manage_subgroups'])
def delete_subgroup(request, subgroup_id):
    subgroup = get_object_or_404(SubGroup, id=subgroup_id)
    if request.method == 'POST':
        subgroup.delete()
        messages.success(request, 'SubGroup successfully deleted!')
        return redirect('core:subgroup_list')
    return render(request, 'core/confirm_delete_subgroup.html', {'subgroup': subgroup})

@login_required
def toggle_theme(request):
    """
    View for theme switch
    """
    if request.method == 'POST':
        user = request.user
        if user.theme_preference == 'light':
            user.theme_preference = 'dark'
        else:
            user.theme_preference = 'light'
        user.save()
        messages.success(request, f'Theme switched to {user.get_theme_preference_display()}.')
        return redirect(request.META.get('HTTP_REFERER', 'dashboard'))
    else:
        return HttpResponseForbidden('Only POST requests are allowed.')

@require_GET
def get_subgroups(request):
    group_ids = request.GET.getlist('group_ids[]')
    subgroups = SubGroup.objects.filter(group__id__in=group_ids).values('id', 'name', 'group__id')
    subgroups_data = {}
    for subgroup in subgroups:
        group_id = subgroup['group__id']
        if group_id not in subgroups_data:
            subgroups_data[group_id] = []
        subgroups_data[group_id].append({'id': subgroup['id'], 'name': subgroup['name']})
    return JsonResponse({'subgroups': subgroups_data})

@login_required
def tag_autocomplete(request):
    if 'q' in request.GET:
        q = request.GET.get('q')
        tags = Tag.objects.filter(name__icontains=q).order_by('name')[:10]
        results = [{'id': tag.id, 'text': tag.name} for tag in tags]
        return JsonResponse({'results': results})
    return JsonResponse({'results': []})

@login_required
@any_permission_required(['core.manage_tags'])
def tag_list(request):
    tags = Tag.objects.all().order_by('name')
    return render(request, 'core/tag_list.html', {'tags': tags})

@login_required
@any_permission_required(['core.manage_tags'])
def tag_create(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag created successfully.')
            return redirect('core:tag_list')
    else:
        form = TagForm()
    return render(request, 'core/tag_form.html', {'form': form, 'title': 'Create Tag'})

@login_required
@any_permission_required(['core.manage_tags'])
def tag_edit(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag updated successfully.')
            return redirect('core:tag_list')
    else:
        form = TagForm(instance=tag)
    return render(request, 'core/tag_form.html', {'form': form, 'title': 'Edit Tag'})

@login_required
@any_permission_required(['core.manage_tags'])
def tag_delete(request, tag_id):
    tag = get_object_or_404(Tag, id=tag_id)
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Tag deleted successfully.')
        return redirect('core:tag_list')
    return render(request, 'core/tag_confirm_delete.html', {'tag': tag})

@csrf_protect
@login_required
def ajax_create_tag(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        logger.info(f"AJAX request to create tag with name: {name}")
        if name:
            tag, created = Tag.objects.get_or_create(name=name)
            if created:
                logger.info(f"Tag '{name}' created successfully.")
                return JsonResponse({'success': True, 'tag': {'id': tag.id, 'name': tag.name}})
            else:
                logger.info(f"Tag '{name}' already exists.")
                return JsonResponse({'success': False, 'error': 'Tag already exists.'})
        else:
            logger.info("Empty tag name received.")
            return JsonResponse({'success': False, 'error': 'Tag name cannot be empty.'})
    logger.info("Invalid request method for ajax_create_tag.")
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

@login_required
def api_keys_list(request):
    """
    View to list all API keys of the logged-in user.
    """
    tokens = BearerToken.objects.filter(user=request.user).order_by('-created_at')
    create_form = APIKeyCreateForm()
    return render(request, 'core/api_keys.html', {
        'tokens': tokens,
        'create_form': create_form,
    })

@login_required
def create_api_key(request):
    """
    View to generate a new API key.
    """
    if request.method == 'POST':
        form = APIKeyCreateForm(request.POST)
        if form.is_valid():
            # Generate a unique token
            new_token = str(uuid.uuid4())
            expires_at = timezone.now() + timedelta(days=30)  # Set expiration as needed
            BearerToken.objects.create(
                token=new_token,
                user=request.user,
                expires_at=expires_at,
                status='active'
            )
            messages.success(request, f'API Key created successfully: {new_token}')
            return redirect('core:api_keys_list')
        else:
            messages.error(request, 'Please confirm to create a new API key.')
            return redirect('core:api_keys_list')
    else:
        return redirect('core:api_keys_list')

@login_required
def revoke_api_key(request, token_id):
    """
    View to revoke an existing API key.
    """
    token = get_object_or_404(BearerToken, id=token_id, user=request.user)
    if token.status == 'revoked':
        messages.info(request, 'This API key is already revoked.')
    else:
        token.status = 'revoked'
        token.save()
        messages.success(request, 'API Key revoked successfully.')
    return redirect('core:api_keys_list')

# List Maintenance
@login_required
@any_permission_required(['core.manage_maintenance'])
def maintenance_list(request):
    maintenances = Maintenance.objects.all()
    logger.info(f"All Maintenances: {maintenances}")
    return render(request, 'core/maintenance_list.html', {'maintenances': maintenances})

# Create Maintenance
@login_required
@any_permission_required(['core.manage_maintenance'])
def maintenance_create(request):
    if request.method == 'POST':
        form = MaintenanceForm(request.POST, user=request.user)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.created_by = request.user
            maintenance.save()
            form.save_m2m()
            messages.success(request, 'Maintenance created successfully.')
            return redirect('core:maintenance_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MaintenanceForm(user=request.user)
    return render(request, 'core/maintenance_form.html', {'form': form, 'title': 'Create Maintenance'})

# Edit Maintenance
@login_required
@any_permission_required(['core.manage_maintenance'])
def maintenance_edit(request, maintenance_id):
    maintenance = get_object_or_404(Maintenance, id=maintenance_id)

    if request.method == 'POST':
        form = MaintenanceForm(request.POST, instance=maintenance, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Maintenance updated successfully.')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            else:
                return redirect('core:maintenance_list')
        else:
            messages.error(request, 'Please correct the errors below.')
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                html = render_to_string('core/maintenance_form_partial.html',
                                        {'form': form, 'maintenance': maintenance}, request=request)
                return JsonResponse({'success': False, 'html': html})
    else:
        form = MaintenanceForm(instance=maintenance, user=request.user)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string('core/maintenance_form_partial.html', {'form': form, 'maintenance': maintenance},
                                    request=request)
            return JsonResponse({'success': True, 'html': html})
        else:
            return render(request, 'core/maintenance_form.html', {'form': form, 'title': 'Edit Maintenance'})

# Delete Maintenance
@login_required
@any_permission_required(['core.manage_maintenance'])
def maintenance_delete(request, maintenance_id):
    maintenance = get_object_or_404(Maintenance, id=maintenance_id)
    if request.method == 'POST':
        maintenance.delete()
        messages.success(request, 'Maintenance deleted successfully.')
        return redirect('core:maintenance_list')
    return render(request, 'core/maintenance_confirm_delete.html', {'maintenance': maintenance})

# JSON Endpoint for Calendar
@login_required
@any_permission_required(['core.manage_maintenance'])
def maintenance_events_json(request):
    maintenances = Maintenance.objects.filter(
        Q(status='scheduled') | Q(status='completed') | Q(status='partially_completed')
    )
    events = []
    for maintenance in maintenances:
        event = {
            'id': maintenance.id,
            'title': maintenance.title,
            'start': maintenance.start_time.isoformat(),
            'end': maintenance.end_time.isoformat(),
            'color': get_event_color(maintenance.status),
            'extendedProps': {
                'description': maintenance.description,
                'status': maintenance.get_status_display(),
                'executive': maintenance.executive.get_full_name() if maintenance.executive else '',
                'service_buttons': [btn.name for btn in maintenance.service_buttons.all()],
            },
        }
        events.append(event)
    return JsonResponse(events, safe=False)

def get_event_color(status):
    colors = {
        'scheduled': '#007bff',  # Blue
        'canceled': '#dc3545',   # Red
        'completed': '#28a745',  # Green
        'partially_completed': '#ffc107',  # Yellow
        'in_progress': '#17a2b8',  # Teal
    }
    return colors.get(status, '#6c757d')  # Default Gray

@login_required
@any_permission_required(['core.manage_maintenance'])
def calendar_view(request):
    form = MaintenanceForm(user=request.user)
    return render(request, 'core/calendar.html', {'form': form})

@login_required
@require_POST
def change_environment(request):
    try:
        data = json.loads(request.body)
        environment_id = data.get('environment_id')

        if not environment_id:
            return JsonResponse({'success': False, 'error': 'Environment ID not select.'}, status=400)

        environment = Environment.objects.get(id=environment_id)

        if request.user.is_staff or environment in request.user.environments.all():
            request.user.current_environment = environment
            request.user.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'You are not have access to selected environment.'}, status=403)

    except Environment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Environment not found.'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Wrong JSON format.'}, status=400)
    except Exception as e:
        logger.error(f"Error in switching environment: {e}")
        return JsonResponse({'success': False, 'error': 'Internal Error.'}, status=500)