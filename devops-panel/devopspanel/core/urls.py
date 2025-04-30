from django.urls import path, include
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard_view, name='devops_dashboard'),
    path('add/', views.add_button, name='add_button'),
    path('edit/<int:button_id>/', views.edit_button, name='edit_button'),
    path('delete/<int:button_id>/', views.delete_button, name='delete_button'),
    # Groups
    path('groups/', views.group_list, name='group_list'),
    path('groups/add/', views.add_group, name='add_group'),
    path('groups/edit/<int:group_id>/', views.edit_group, name='edit_group'),
    path('groups/delete/<int:group_id>/', views.delete_group, name='delete_group'),
    # Environments
    path('environments/', views.environment_list, name='environment_list'),
    path('environments/add/', views.add_environment, name='add_environment'),
    path('environments/edit/<int:environment_id>/', views.edit_environment, name='edit_environment'),
    path('environments/delete/<int:environment_id>/', views.delete_environment, name='delete_environment'),
    # Infrastructure Data
    path('infrastructure/data/', views.infrastructure_data, name='infrastructure_data'),
    # Trigger Error
    path('trigger-error/', views.trigger_error, name='trigger_error'),
    # API Endpoints
    path('api/token/', views.obtain_bearer_token, name='obtain_bearer_token'),
    path('api/update_version/', views.update_version, name='update_version'),
    path('api/revoke_token/', views.revoke_token, name='revoke_token'),
    path('subgroups/', views.subgroup_list, name='subgroup_list'),
    path('get_subgroups/', views.subgroup_list, name='get_subgroups'),
    path('subgroups/add/', views.add_subgroup, name='add_subgroup'),
    path('subgroups/edit/<int:subgroup_id>/', views.edit_subgroup, name='edit_subgroup'),
    path('subgroups/delete/<int:subgroup_id>/', views.delete_subgroup, name='delete_subgroup'),
    path('api-keys/', views.api_keys_list, name='api_keys_list'),
    path('api-keys/create/', views.create_api_key, name='create_api_key'),
    path('api-keys/revoke/<int:token_id>/', views.revoke_api_key, name='revoke_api_key'),
    # Theme Toggle
    path('toggle-theme/', views.toggle_theme, name='toggle_theme'),
    # Tags
    path('tags/autocomplete/', views.tag_autocomplete, name='tag_autocomplete'),
    path('tags/create/', views.tag_create, name='tag_create'),
    path('tags/ajax/create/', views.ajax_create_tag, name='ajax_create_tag'),
    path('tags/', views.tag_list, name='tag_list'),
    path('tags/<int:tag_id>/edit/', views.tag_edit, name='tag_edit'),
    path('tags/<int:tag_id>/delete/', views.tag_delete, name='tag_delete'),
    # Maintenances
    path('maintenances/', views.maintenance_list, name='maintenance_list'),
    path('maintenances/create/', views.maintenance_create, name='maintenance_create'),
    path('maintenances/edit/<int:maintenance_id>/', views.maintenance_edit, name='maintenance_edit'),
    path('maintenances/delete/<int:maintenance_id>/', views.maintenance_delete, name='maintenance_delete'),
    path('maintenances/events/json/', views.maintenance_events_json, name='maintenance_events_json'),
    # Calendar
    path('calendar/', views.calendar_view, name='calendar'),
    path('change-environment/', views.change_environment, name='change_environment'),

]