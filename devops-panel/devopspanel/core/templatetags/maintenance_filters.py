# core/templatetags/maintenance_filters.py

from django import template

register = template.Library()

@register.filter(name='filter_maintenances')
def filter_maintenances(maintenances, button):
    return maintenances.filter(service_buttons=button)
