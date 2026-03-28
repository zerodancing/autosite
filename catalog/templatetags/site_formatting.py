from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def spaced_number(value):
    if value in (None, ""):
        return ""

    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return value

    if decimal_value == decimal_value.to_integral_value():
        formatted = f"{int(decimal_value):,}"
    else:
        formatted = f"{decimal_value:,.2f}".rstrip("0").rstrip(".")
    return formatted.replace(",", " ")
