from django import template

register = template.Library()

@register.inclusion_tag('dashboard/dependency_tree.html')
def render_dependency_tree(dependencies):
    return {'dependencies': dependencies}
