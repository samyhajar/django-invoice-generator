from django.test import TestCase
from decimal import Decimal
from invoices.models import TaxYear, TaxBracket
from invoices.utils import calculate_progressive_tax

class TaxCalculationTests(TestCase):
    def setUp(self):
        # Setup 2025 brackets same as production script
        self.year = TaxYear.objects.create(year=2025, active=True)
        
        brackets = [
            (0, 13308, 0),
            (13308, 20818, 20),
            (20818, 34513, 30),
            (34513, 66612, 40),
            (66612, 99266, 48),
            (99266, 1000000, 50),
            (1000000, None, 55),
        ]
        
        for lower, upper, rate in brackets:
            TaxBracket.objects.create(
                tax_year=self.year,
                lower_limit=Decimal(lower),
                upper_limit=Decimal(upper) if upper else None,
                rate=Decimal(rate)
            )

    def test_zero_income(self):
        result = calculate_progressive_tax(0, 2025)
        self.assertEqual(result['total_tax'], Decimal('0.00'))

    def test_first_bracket_limit(self):
        # 13,308 income -> 0 tax
        result = calculate_progressive_tax(13308, 2025)
        self.assertEqual(result['total_tax'], Decimal('0.00'))

    def test_second_bracket(self):
        # 14,000 income
        # 13,308 is free. 692 taxed at 20%
        # 692 * 0.20 = 138.40
        income = 14000
        result = calculate_progressive_tax(income, 2025)
        expected_tax = (Decimal(income) - Decimal(13308)) * Decimal('0.20')
        self.assertEqual(result['total_tax'], expected_tax)

    def test_third_bracket_entry(self):
        # 21,000 income
        # 0-13308 (13308) @ 0% = 0
        # 13308-20818 (7510) @ 20% = 1502
        # 20818-21000 (182) @ 30% = 54.6
        # Total = 1556.6
        income = 21000
        result = calculate_progressive_tax(income, 2025)
        
        tax_bracket_2 = Decimal(7510) * Decimal('0.20')
        tax_bracket_3 = (Decimal(income) - Decimal(20818)) * Decimal('0.30')
        expected = tax_bracket_2 + tax_bracket_3
        
        self.assertAlmostEqual(result['total_tax'], expected, places=2)

    def test_high_income(self):
        # 2,000,000 income
        # Should hit all brackets
        result = calculate_progressive_tax(2000000, 2025)
        self.assertTrue(result['total_tax'] > 0)
        self.assertTrue(len(result['brackets']) == 7) # All 7 brackets used
