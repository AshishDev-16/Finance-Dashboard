from django import template

register = template.Library()

@register.filter(name='abs_value')
def abs_value(value):
    return abs(value) 