from django import template

register = template.Library()


@register.filter(name='python_all')
def python_all(values):
    return all(values)

@register.filter(name='python_any')
def python_any(values):
    return any(values)