from django import template

from budgetbuddy.constants import CATEGORY_ICON_CLASSES, TRANSACTION_ICON_CLASSES

register = template.Library()


@register.filter
def transaction_icon(icon_key):
    return TRANSACTION_ICON_CLASSES.get(icon_key, TRANSACTION_ICON_CLASSES['default'])


@register.filter
def category_icon(category_name):
    return CATEGORY_ICON_CLASSES.get(category_name, CATEGORY_ICON_CLASSES['default'])
