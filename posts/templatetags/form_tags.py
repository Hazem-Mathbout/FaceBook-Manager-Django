# templatetags/form_tags.py

from django import template

register = template.Library()

@register.filter(name='as_bootstrap')
def as_bootstrap(field):
    return field.as_widget(attrs={'class': 'form-control'})
