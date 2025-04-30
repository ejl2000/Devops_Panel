from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from devopspanel.core.models import ServiceButton
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseForbidden
from devopspanel.dashboard.forms import CustomUserCreationForm, CustomUserChangeForm, RoleForm, PermissionForm, UserProfileForm, CustomPasswordChangeForm
from .models import Role, Permission, CustomUser
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.http import require_POST, require_GET
import logging
import pprint

logger = logging.getLogger(__name__)

User = get_user_model()

def is_admin(user):
    return user.is_staff

# Add User View
@login_required
@user_passes_test(is_admin)
def add_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            user.environments.set(form.cleaned_data['environments'])
            user.service_groups.set(form.cleaned_data['service_groups'])
            messages.success(request, 'User successfully created!')
            return redirect('users:user_list')
        else:
            messages.error(request, 'Please re-check errors in the form.')
    else:
        form = CustomUserCreationForm()
    context = {
        'form': form,
        'title': 'Add User',
        'submit_text': 'Create User',
        'cancel_url': 'users:user_list',
        'show_password_fields': True,
    }
    return render(request, 'users/user_form.html', context)

# Edit User View
@login_required
@user_passes_test(is_admin)
def edit_user(request, user_id):
    user_obj = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, request.FILES, instance=user_obj)
        if form.is_valid():
            form.save()
            user_obj.environments.set(form.cleaned_data['environments'])
            user_obj.service_groups.set(form.cleaned_data['service_groups'])
            messages.success(request, 'User successfully edited!')
            return redirect('users:user_list')
        else:
            messages.error(request, 'Please re-check errors in the form.')
    else:
        form = CustomUserChangeForm(instance=user_obj)
    context = {
        'form': form,
        'user_obj': user_obj,
        'title': f'Edit User: "{user_obj.username}"',
        'submit_text': 'Save Changes',
        'cancel_url': 'users:user_list',
        'show_password_fields': False,
    }
    return render(request, 'users/user_form.html', context)

# Delete User View
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User successfully deleted!')
        return redirect('core:user_list')
    return render(request, 'users/confirm_delete_user.html', {'user_obj': user})

@user_passes_test(is_admin)
def user_list(request):
    users = User.objects.all().prefetch_related('roles', 'environments').order_by('-username')
    paginator = Paginator(users, 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        rendered_users = ''.join([
            render_to_string('users/user_list_partials.html', {'user': user}, request=request)
            for user in page_obj
        ])
        return JsonResponse({'html': rendered_users, 'has_next': page_obj.has_next()})

    return render(request, 'users/user_list.html', {'users': page_obj})

@user_passes_test(is_admin)
@require_GET
def get_user_statuses(request):
    user_ids = request.GET.getlist('user_ids[]')
    if not user_ids:
        return JsonResponse({'error': 'No user IDs provided'}, status=400)

    users = User.objects.filter(id__in=user_ids)
    statuses = {user.id: user.is_online() for user in users}
    return JsonResponse({'statuses': statuses})

@user_passes_test(is_admin)
def role_list(request):
    roles = Role.objects.all()
    return render(request, 'users/role_list.html', {'roles': roles})

@login_required
@user_passes_test(is_admin)
def add_role(request):
    if request.method == 'POST':
        form = RoleForm(request.POST, cancel_url=reverse('users:role_list'))
        if form.is_valid():
            form.save()
            messages.success(request, 'Role successfully created!')
            return redirect('users:role_list')
        else:
            messages.error(request, 'Please re-check errors in the form.')
    else:
        form = RoleForm(cancel_url=reverse('users:role_list'))
    context = {
        'form': form,
        'title': 'Add Role',
        'submit_text': 'Create Role',
        'cancel_url': 'users:role_list'
    }
    return render(request, 'users/role_form.html', context)

@login_required
@user_passes_test(is_admin)
def edit_role(request, role_id):
    role = get_object_or_404(Role, id=role_id)
    if request.method == 'POST':
        form = RoleForm(request.POST, instance=role, cancel_url=reverse('users:role_list'))
        if form.is_valid():
            form.save()
            messages.success(request, 'Role successfully edited!')
            return redirect('users:role_list')
        else:
            messages.error(request, 'Please re-check errors in the form.')
    else:
        form = RoleForm(instance=role, cancel_url=reverse('users:role_list'))
    context = {
        'form': form,
        'role': role,
        'title': f'Edit Role: "{role.name}"',
        'submit_text': 'Save Changes',
        'cancel_url': 'users:role_list'
    }
    return render(request, 'users/role_form.html', context)

@user_passes_test(is_admin)
def delete_role(request, role_id):
    role = get_object_or_404(Role, id=role_id)
    if request.method == 'POST':
        role.delete()
        messages.success(request, 'Role successfully Deleted!')
        return redirect('core:role_list')
    return render(request, 'users/confirm_delete_role.html', {'role': role})

@user_passes_test(is_admin)
def permission_list(request):
    search_query = request.GET.get('search', '').strip()
    sort_by = request.GET.get('sort', 'name')

    permissions = Permission.objects.all()

    if search_query:
        permissions = permissions.filter(
            Q(name__icontains=search_query) |
            Q(codename__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    if sort_by in ['name', 'codename']:
        permissions = permissions.order_by(sort_by)

    return render(request, 'users/permission_list.html', {
        'permissions': permissions,
        'search_query': search_query,
        'sort_by': sort_by
    })


@user_passes_test(is_admin)
def add_permission(request):
    if request.method == 'POST':
        form = PermissionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Permission Successfully Added!')
            return redirect('core:permission_list')
        else:
            messages.error(request, 'Check errors in the form.')
    else:
        form = PermissionForm()
    return render(request, 'users/add_permission.html', {'form': form})


@user_passes_test(is_admin)
def edit_permission(request, permission_id):
    permission = get_object_or_404(Permission, id=permission_id)
    if request.method == 'POST':
        form = PermissionForm(request.POST, instance=permission)
        if form.is_valid():
            form.save()
            messages.success(request, 'Permission Successfully Updated!')
            return redirect('core:permission_list')
        else:
            messages.error(request, 'Check errors in the form.')
    else:
        form = PermissionForm(instance=permission)
    return render(request, 'users/edit_permission.html', {'form': form, 'permission': permission})


@user_passes_test(is_admin)
def delete_permission(request, permission_id):
    permission = get_object_or_404(Permission, id=permission_id)
    if request.method == 'POST':
        permission.delete()
        messages.success(request, 'Permission Successfully Deleted!')
        return redirect('users:permission_list')
    return render(request, 'users/confirm_delete_permission.html', {'permission': permission})

def get_location_icons():
    return {
        'K8S': 'icons/kubernetes.svg',
        'VM-GCP': 'icons/google_cloud.svg',
        'Cloud-SQL': 'icons/google_cloud_sql.svg',
        'CloudFlare': 'icons/cloudflare.svg',
        'AWS': 'icons/aws.svg',
        'Bare-Metal': 'icons/bare_metal.svg',
    }

def get_dev_language_icons():
    return {
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

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(user=user, data=request.POST)
            profile_form = UserProfileForm(instance=user)
            current_password = request.POST.get('current_password')
            if not current_password:
                password_form.add_error(None, 'Please enter your current password.')
                messages.error(request, 'Please correct the errors below.')
            elif not user.check_password(current_password):
                password_form.add_error(None, 'Incorrect current password.')
                messages.error(request, 'Please correct the errors below.')
            elif password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Your password was successfully updated!')
                logger.debug("Password changed successfully for user: %s", user.username)
                return redirect('users:profile')
            else:
                logger.debug("Password change form errors: %s", password_form.errors)
                messages.error(request, 'Please correct the errors below.')
        else:
            profile_form = UserProfileForm(request.POST, request.FILES, instance=user)
            password_form = CustomPasswordChangeForm(user=user)
            current_password = request.POST.get('current_password')
            if not current_password:
                profile_form.add_error(None, 'Please enter your current password.')
                messages.error(request, 'Please correct the errors below.')
            elif not user.check_password(current_password):
                profile_form.add_error(None, 'Incorrect current password.')
                messages.error(request, 'Please correct the errors below.')
            elif profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Your profile was successfully updated!')
                logger.debug("Profile updated successfully for user: %s", user.username)
                return redirect('users:profile')
            else:
                logger.debug("Profile update form errors: %s", profile_form.errors)
                messages.error(request, 'Please correct the errors below.')
    else:
        profile_form = UserProfileForm(instance=user)
        password_form = CustomPasswordChangeForm(user=user)

    group_ids = request.GET.getlist('group')
    tag_ids = request.GET.getlist('tag')
    search_query = request.GET.get('search', '').strip()

    user_service_buttons = ServiceButton.objects.filter(created_by=user).prefetch_related('groups', 'subgroup', 'tags')

    if group_ids:
        user_service_buttons = user_service_buttons.filter(groups__id__in=group_ids)
    if tag_ids:
        user_service_buttons = user_service_buttons.filter(tags__id__in=tag_ids)
    if search_query:
        user_service_buttons = user_service_buttons.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        ).distinct()

    grouped_buttons = {}
    for button in user_service_buttons:
        for group in button.groups.all():
            if group.id not in grouped_buttons:
                grouped_buttons[group.id] = {
                    'group': group,
                    'subgroups': {}
                }
            subgroup_name = button.subgroup.name if button.subgroup else 'No SubGroup'
            if subgroup_name not in grouped_buttons[group.id]['subgroups']:
                grouped_buttons[group.id]['subgroups'][subgroup_name] = []
            grouped_buttons[group.id]['subgroups'][subgroup_name].append(button)
            logger.debug(f"Button '{button.name}' added to group '{group.name}' under subgroup '{subgroup_name}'")

    user_service_buttons_ids = user_service_buttons.values_list('id', flat=True)
    inframap_buttons_queryset = ServiceButton.objects.filter(
        id__in=user_service_buttons_ids
    ).prefetch_related('connections', 'groups', 'subgroup')

    inframap_buttons = []
    for button in inframap_buttons_queryset:
        inframap_buttons.append({
            'id': button.id,
            'name': button.name,
            'description': button.description,
            'url': button.url,
            'ip': button.ip,
            'port': button.port,
            'version': button.version,
            'location': button.location,
            'dev_language': button.dev_language,
            'executive': f"{button.executive.first_name} {button.executive.last_name}" if button.executive else '',
            'tags': list(button.tags.values_list('name', flat=True)),
            'groups': list(button.groups.values('id', 'name')),
            'subgroup': {
                'id': button.subgroup.id,
                'name': button.subgroup.name
            } if button.subgroup else None,
        })

    inframap_connections = []
    for button in inframap_buttons_queryset:
        for connected_button in button.connections.all():
            if connected_button.id in user_service_buttons_ids:
                inframap_connections.append({
                    'source': button.id,
                    'target': connected_button.id
                })

    location_icons = get_location_icons()
    dev_language_icons = get_dev_language_icons()

    logger.info(f"User '{user.username}' has {user_service_buttons.count()} ServiceButtons after filtering.")
    logger.info(f"Grouped Buttons Structure: {pprint.pformat(grouped_buttons)}")
    logger.info(f"Inframap Connections: {inframap_connections}")

    return render(request, 'users/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'grouped_buttons': grouped_buttons,
        'inframap_buttons': inframap_buttons,
        'inframap_connections': inframap_connections,
        'location_icons': location_icons,
        'dev_language_icons': dev_language_icons,
    })