from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
import devopspanel.users.views

app_name = "users"
urlpatterns = [
    # Permissions
    path('permissions/', views.permission_list, name='permission_list'),
    path('add_permission/', views.add_permission, name='add_permission'),
    path('permissions/edit/<int:permission_id>/', views.edit_permission, name='edit_permission'),
    path('permissions/delete/<int:permission_id>/', views.delete_permission, name='delete_permission'),
    # Users
    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('profile/', views.profile_view, name='profile'),
    path('users/statuses/', views.get_user_statuses, name='get_user_statuses'),
    # Roles
    path('roles/', views.role_list, name='role_list'),
    path('roles/add/', views.add_role, name='add_role'),
    path('roles/edit/<int:role_id>/', views.edit_role, name='edit_role'),
    path('roles/delete/<int:role_id>/', views.delete_role, name='delete_role'),
    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='users:login'), name='logout'),
]
