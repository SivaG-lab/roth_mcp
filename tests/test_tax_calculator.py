"""
T009 — Tests for federal + state tax calculation.

Tests cover:
  - compute_federal_tax: progressive bracket calculation for all 4 filing statuses
  - compute_state_tax: flat-rate state tax on Roth conversion amount
  - Standard deduction application (taxable_income = gross - deduction)
  - Bracket boundary crossing
  - Edge cases: zero income, deduction exceeds income
"""

import pytest
from tax.brackets import compute_federal_tax, FEDERAL_BRACKETS, STANDARD_DEDUCTIONS
from tax.state_rates import compute_state_tax


# ---------------------------------------------------------------------------
# Standard deduction constants (2024)
# ---------------------------------------------------------------------------

class TestStandardDeductions:
    """Verify the standard deduction constants are correct for 2024."""

    def test_single_deduction(self):
        assert STANDARD_DEDUCTIONS["single"] == 14_600

    def test_married_joint_deduction(self):
        assert STANDARD_DEDUCTIONS["married_joint"] == 29_200

    def test_married_separate_deduction(self):
        assert STANDARD_DEDUCTIONS["married_separate"] == 14_600

    def test_head_of_household_deduction(self):
        assert STANDARD_DEDUCTIONS["head_of_household"] == 21_900


# ---------------------------------------------------------------------------
# Federal brackets sanity checks
# ---------------------------------------------------------------------------

class TestFederalBrackets:
    """Verify the bracket definitions exist and have the right structure."""

    def test_married_joint_brackets_exist(self):
        brackets = FEDERAL_BRACKETS["married_joint"]
        assert len(brackets) == 7
        # First bracket: (23200, 0.10)
        assert brackets[0] == (23_200, 0.10)
        # Last bracket: (inf, 0.37)
        assert brackets[-1][1] == 0.37

    def test_all_filing_statuses_present(self):
        for status in ("single", "married_joint", "married_separate", "head_of_household"):
            assert status in FEDERAL_BRACKETS, f"Missing brackets for {status}"


# ---------------------------------------------------------------------------
# Federal tax — zero / trivial cases
# ---------------------------------------------------------------------------

class TestFederalTaxZeroCases:
    """Zero and below-zero taxable income should produce zero tax."""

    def test_zero_taxable_income_single(self):
        assert compute_federal_tax(0, "single") == 0.0

    def test_zero_taxable_income_married_joint(self):
        assert compute_federal_tax(0, "married_joint") == 0.0

    def test_negative_taxable_income_returns_zero(self):
        # If deduction exceeds gross, taxable could be negative — tax should be 0
        assert compute_federal_tax(-5_000, "single") == 0.0


# ---------------------------------------------------------------------------
# Federal tax — single filer bracket boundaries (2024)
# ---------------------------------------------------------------------------
# Single brackets 2024:
#   (11600, 0.10), (47150, 0.12), (100525, 0.22), (191950, 0.24),
#   (243725, 0.32), (609350, 0.35), (inf, 0.37)

class TestFederalTaxSingleBrackets:
    """Progressive bracket math for single filers."""

    def test_entirely_in_10_percent_bracket(self):
        # $10,000 taxable → all at 10%
        expected = 10_000 * 0.10
        assert compute_federal_tax(10_000, "single") == pytest.approx(expected, abs=0.01)

    def test_at_first_bracket_boundary(self):
        # Exactly $11,600 → all at 10%
        expected = 11_600 * 0.10
        assert compute_federal_tax(11_600, "single") == pytest.approx(expected, abs=0.01)

    def test_crossing_into_12_percent_bracket(self):
        # $47,150 taxable (top of 12% bracket)
        expected = 11_600 * 0.10 + (47_150 - 11_600) * 0.12
        assert compute_federal_tax(47_150, "single") == pytest.approx(expected, abs=0.01)

    def test_crossing_into_22_percent_bracket(self):
        # $100,525 taxable (top of 22% bracket)
        expected = (
            11_600 * 0.10
            + (47_150 - 11_600) * 0.12
            + (100_525 - 47_150) * 0.22
        )
        assert compute_federal_tax(100_525, "single") == pytest.approx(expected, abs=0.01)

    def test_mid_24_percent_bracket(self):
        # $150,000 taxable — partway through 24% bracket
        expected = (
            11_600 * 0.10
            + (47_150 - 11_600) * 0.12
            + (100_525 - 47_150) * 0.22
            + (150_000 - 100_525) * 0.24
        )
        assert compute_federal_tax(150_000, "single") == pytest.approx(expected, abs=0.01)

    def test_crossing_into_32_percent_bracket(self):
        # $191,950 — top of 24%
        expected = (
            11_600 * 0.10
            + (47_150 - 11_600) * 0.12
            + (100_525 - 47_150) * 0.22
            + (191_950 - 100_525) * 0.24
        )
        assert compute_federal_tax(191_950, "single") == pytest.approx(expected, abs=0.01)


# ---------------------------------------------------------------------------
# Federal tax — married filing jointly (2024)
# ---------------------------------------------------------------------------
# MFJ brackets 2024:
#   (23200, 0.10), (94300, 0.12), (201050, 0.22), (383900, 0.24),
#   (487450, 0.32), (731200, 0.35), (inf, 0.37)

class TestFederalTaxMFJ:
    """Progressive bracket math for married filing jointly."""

    def test_mfj_all_in_10_percent(self):
        expected = 20_000 * 0.10
        assert compute_federal_tax(20_000, "married_joint") == pytest.approx(expected, abs=0.01)

    def test_mfj_crossing_12_percent(self):
        # $94,300 — top of 12%
        expected = 23_200 * 0.10 + (94_300 - 23_200) * 0.12
        assert compute_federal_tax(94_300, "married_joint") == pytest.approx(expected, abs=0.01)

    def test_mfj_150k_income_plus_50k_conversion_scenario(self):
        """Core scenario: $150k ordinary + $50k conversion = $200k gross, MFJ.
        Taxable = 200000 - 29200 = 170800.
        """
        taxable = 200_000 - 29_200  # 170_800
        expected = (
            23_200 * 0.10
            + (94_300 - 23_200) * 0.12
            + (170_800 - 94_300) * 0.22
        )
        assert compute_federal_tax(taxable, "married_joint") == pytest.approx(expected, abs=0.01)

    def test_mfj_high_income_in_37_percent(self):
        # $800,000 taxable — into the 37% bracket
        expected = (
            23_200 * 0.10
            + (94_300 - 23_200) * 0.12
            + (201_050 - 94_300) * 0.22
            + (383_900 - 201_050) * 0.24
            + (487_450 - 383_900) * 0.32
            + (731_200 - 487_450) * 0.35
            + (800_000 - 731_200) * 0.37
        )
        assert compute_federal_tax(800_000, "married_joint") == pytest.approx(expected, abs=0.01)


# ---------------------------------------------------------------------------
# Federal tax — married filing separately
# ---------------------------------------------------------------------------

class TestFederalTaxMarriedSeparate:
    """Married filing separately has its own bracket set."""

    def test_mfs_zero(self):
        assert compute_federal_tax(0, "married_separate") == 0.0

    def test_mfs_basic(self):
        # Just confirm it runs without error for a mid-range income
        result = compute_federal_tax(80_000, "married_separate")
        assert result > 0


# ---------------------------------------------------------------------------
# Federal tax — head of household
# ---------------------------------------------------------------------------

class TestFederalTaxHOH:
    """Head of household has its own bracket set."""

    def test_hoh_zero(self):
        assert compute_federal_tax(0, "head_of_household") == 0.0

    def test_hoh_basic(self):
        result = compute_federal_tax(60_000, "head_of_household")
        assert result > 0


# ---------------------------------------------------------------------------
# State tax
# ---------------------------------------------------------------------------

class TestStateTax:
    """State tax is a flat rate applied to the conversion amount."""

    def test_california_rate(self):
        # CA top marginal ≈ 9.3% for most Roth conversion scenarios
        tax = compute_state_tax(50_000, "CA")
        expected = 50_000 * 0.093
        assert tax == pytest.approx(expected, abs=0.01)

    def test_zero_conversion(self):
        assert compute_state_tax(0, "CA") == 0.0

    def test_no_income_tax_state(self):
        # Texas has no state income tax
        assert compute_state_tax(100_000, "TX") == 0.0

    def test_negative_conversion_returns_zero(self):
        assert compute_state_tax(-10_000, "CA") == 0.0


# ---------------------------------------------------------------------------
# Integration: standard deduction then federal tax
# ---------------------------------------------------------------------------

class TestStandardDeductionIntegration:
    """Verify the pattern: taxable = max(gross - deduction, 0) → fed tax."""

    def test_deduction_exceeds_gross(self):
        gross = 10_000
        deduction = STANDARD_DEDUCTIONS["single"]  # 14600
        taxable = max(gross - deduction, 0)
        assert taxable == 0
        assert compute_federal_tax(taxable, "single") == 0.0

    def test_deduction_applied_mfj(self):
        gross = 200_000
        deduction = STANDARD_DEDUCTIONS["married_joint"]  # 29200
        taxable = gross - deduction  # 170800
        assert taxable == 170_800
        tax = compute_federal_tax(taxable, "married_joint")
        assert tax > 0
