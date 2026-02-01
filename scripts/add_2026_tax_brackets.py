import django
import os
import sys
from decimal import Decimal

# Setup Django environment
sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from invoices.models import TaxYear, TaxBracket

def populate_tax_brackets_2026():
    # create 2026 tax year
    year_2026, created = TaxYear.objects.get_or_create(year=2026, defaults={'active': True})
    
    if created:
        print("Created Tax Year 2026")
    else:
        print("Tax Year 2026 already exists")
        
    # Clear existing brackets for this year to avoid duplicates if re-run
    TaxBracket.objects.filter(tax_year=year_2026).delete()

    brackets = [
        # 0 - 13.308 : 0%
        {
            'lower': Decimal('0'),
            'upper': Decimal('13308'),
            'rate': Decimal('0'),
            'description': '0% up to 13.308€'
        },
        # 13.308 - 20.818 : 20%
        {
            'lower': Decimal('13308'),
            'upper': Decimal('20818'),
            'rate': Decimal('20'),
            'description': '20% (13.308-20.818€)'
        },
        # 20.818 - 34.513 : 30%
        {
            'lower': Decimal('20818'),
            'upper': Decimal('34513'),
            'rate': Decimal('30'),
            'description': '30% (20.818-34.513€)'
        },
        # 34.513 - 66.612 : 40%
        {
            'lower': Decimal('34513'),
            'upper': Decimal('66612'),
            'rate': Decimal('40'),
            'description': '40% (34.513-66.612€)'
        },
        # 66.612 - 99.266 : 48%
        {
            'lower': Decimal('66612'),
            'upper': Decimal('99266'),
            'rate': Decimal('48'),
            'description': '48% (66.612-99.266€)'
        },
        # 99.266 - 1.000.000 : 50%
        {
            'lower': Decimal('99266'),
            'upper': Decimal('1000000'),
            'rate': Decimal('50'),
            'description': '50% (99.266-1Mio€)'
        },
        # 1.000.000+ : 55%
        {
            'lower': Decimal('1000000'),
            'upper': None,
            'rate': Decimal('55'),
            'description': '55% (over 1Mio€)'
        }
    ]

    for b in brackets:
        TaxBracket.objects.create(
            tax_year=year_2026,
            lower_limit=b['lower'],
            upper_limit=b['upper'],
            rate=b['rate'],
            description=b['description']
        )
        print(f"Created bracket (2026): {b['description']}")

if __name__ == "__main__":
    populate_tax_brackets_2026()
