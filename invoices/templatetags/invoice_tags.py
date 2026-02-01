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
