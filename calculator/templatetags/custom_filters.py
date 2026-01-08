from django import template

register = template.Library()


@register.filter
def divide(value, arg):
    """Делит value на arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0


@register.filter
def percentage(value):
    """Преобразует десятичную дробь в проценты"""
    try:
        return f"{float(value) * 100:.1f}"
    except (ValueError, TypeError):
        return "0"


@register.filter
def multiply(value, arg):
    """Умножает value на arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def subtract(value, arg):
    """Вычитает arg из value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0