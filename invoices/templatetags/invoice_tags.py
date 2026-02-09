from django import template
import decimal

register = template.Library()

@register.filter(name='currency_de')
def currency_de(value):
    """
    Formats a number as German currency (e.g., 6.000,00).
    """
    if value is None:
        return ""
    
    try:
        # Convert to float/decimal
        if not isinstance(value, (int, float, decimal.Decimal)):
            value = float(value)
            
        # Format with 2 decimal places and dot for thousands
        # Using format() with a custom way since locale can be tricky in some environments
        formatted = "{:,.2f}".format(value)
        # formatted is "6,000.00"
        # Swap , and . for German format
        parts = formatted.split('.')
        # parts[0] is "6,000", parts[1] is "00"
        main_part = parts[0].replace(',', '.')
        decimal_part = parts[1]
        
        return f"{main_part},{decimal_part}"
    except (ValueError, TypeError):
        return value

@register.filter
def is_selected(value, option_value):
    """
    Checks if a field value matches an option value.
    Both are converted to strings for comparison.
    """
    return str(value) == str(option_value)

@register.filter
def render_options(field):
    """
    Renders <option> tags for a form field, marking the selected one.
    """
    from django.utils.safestring import mark_safe
    if not hasattr(field, 'field') or not hasattr(field.field, 'choices'):
        return ""
    
    output = []
    # Get current value, handling potential None
    current_value = field.value()
    if current_value is None:
        current_value = ""
    current_value = str(current_value)
    
    for choice_value, choice_label in field.field.choices:
        selected = 'selected' if str(choice_value) == current_value else ''
        output.append(f'<option value="{choice_value}" {selected}>{choice_label}</option>')
    
    return mark_safe('\n'.join(output))

@register.filter
def is_checked(value):
    """
    Returns 'checked' if the value is truthy.
    Useful for checkboxes to avoid formatting issues with {% if %}.
    """
    return 'checked' if value else ''
