from django import template

register = template.Library()

@register.filter
def get_range(value):
    try:
        return range(int(value))  # Converts value to an integer and returns a range
    except ValueError:
        return range(0)  # Return an empty range if the value is not an integer
