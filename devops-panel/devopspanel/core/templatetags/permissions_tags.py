from django import template

register = template.Library()

@register.filter(name='has_permission')
def has_permission(user_permissions, permission_name):
    app_label = permission_name.split(':')[0]
    wildcard = f"{app_label}:*"
    return permission_name in user_permissions or wildcard in user_permissions