from decimal import Decimal
from .models import TaxYear, TaxBracket

def calculate_progressive_tax(income: Decimal, year: int) -> dict:
    """
    Calculate progressive tax for a given income and year.
    Returns a dict with:
    - total_tax: Decimal
    - brackets: list of dicts with breakdown per bracket
    - effective_rate: Decimal
    """
    try:
        tax_year = TaxYear.objects.get(year=year, active=True)
        brackets = tax_year.brackets.all().order_by('lower_limit')
    except TaxYear.DoesNotExist:
        return {
            'total_tax': Decimal('0.00'),
            'brackets': [],
            'effective_rate': Decimal('0.00'),
            'error': f"Tax year {year} not found or inactive"
        }

    total_tax = Decimal('0.00')
    breakdown = []
    
    # Ensure income is Decimal
    income = Decimal(str(income))

    for bracket in brackets:
        # Determine the amount of income falling into this bracket
        lower = bracket.lower_limit
        upper = bracket.upper_limit
        rate = bracket.rate / Decimal('100')
        
        if income <= lower:
            # Income doesn't reach this bracket
            break
            
        # Calculate taxable amount in this bracket
        if upper is None:
            # Last bracket (infinite)
            taxable_in_bracket = income - lower
        else:
            if income > upper:
                # Income covers full bracket
                taxable_in_bracket = upper - lower
            else:
                # Income falls within this bracket
                taxable_in_bracket = income - lower
        
        tax_for_bracket = taxable_in_bracket * rate
        total_tax += tax_for_bracket
        
        breakdown.append({
            'bracket': bracket,
            'taxable_amount': taxable_in_bracket,
            'tax_amount': tax_for_bracket,
            'rate': bracket.rate
        })

    effective_rate = (total_tax / income * 100) if income > 0 else Decimal('0.00')

    return {
        'total_tax': total_tax,
        'brackets': breakdown,
        'effective_rate': effective_rate
    }
