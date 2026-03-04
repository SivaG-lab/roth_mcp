"""
T012 — Tests for Social Security benefit taxation.

Tests cover:
  - Provisional income formula: provisional = other_income + 0.5 * ss_benefit
  - Single / head_of_household thresholds: $25k / $34k
  - Married filing jointly thresholds: $32k / $44k
  - Married filing separately: always 85% taxable
  - Below lower threshold: 0% taxable
  - Between thresholds: min(50% of excess over lower, 50% of benefit)
  - Above upper threshold: min(50% of first gap + 85% of excess over upper, 85% of benefit)
  - Zero SS benefit → 0
  - Cap at 85% of benefit

Function signature:
  compute_ss_taxation(ss_benefit, other_income, filing_status) -> taxable_portion
"""

import pytest
from tax.ss import compute_ss_taxation


# ---------------------------------------------------------------------------
# Zero SS benefit — always zero taxable regardless of other income
# ---------------------------------------------------------------------------

class TestSSTaxationZeroBenefit:
    """If there is no SS benefit, taxable portion is zero."""

    def test_zero_benefit_single(self):
        assert compute_ss_taxation(0, 50_000, "single") == 0.0

    def test_zero_benefit_mfj(self):
        assert compute_ss_taxation(0, 100_000, "married_joint") == 0.0

    def test_zero_benefit_married_separate(self):
        assert compute_ss_taxation(0, 80_000, "married_separate") == 0.0


# ---------------------------------------------------------------------------
# Single filer — below lower threshold ($25k)
# ---------------------------------------------------------------------------

class TestSSSingleBelowThreshold:
    """Provisional income < $25,000 → 0% taxable."""

    def test_low_income_low_ss(self):
        # other_income=15000, ss=10000 → provisional = 15000 + 5000 = 20000 < 25000
        assert compute_ss_taxation(10_000, 15_000, "single") == 0.0

    def test_exactly_at_lower_threshold(self):
        # other_income=20000, ss=10000 → provisional = 20000 + 5000 = 25000
        # At the threshold → 0 taxable (not above)
        assert compute_ss_taxation(10_000, 20_000, "single") == 0.0


# ---------------------------------------------------------------------------
# Single filer — between thresholds ($25k–$34k)
# ---------------------------------------------------------------------------

class TestSSSingleBetweenThresholds:
    """$25,000 < provisional <= $34,000 → min(50% of excess, 50% of benefit)."""

    def test_just_above_lower_threshold(self):
        # other_income=22000, ss=10000 → provisional = 22000 + 5000 = 27000
        # excess over 25000 = 2000; 50% of excess = 1000
        # 50% of benefit = 5000
        # taxable = min(1000, 5000) = 1000
        assert compute_ss_taxation(10_000, 22_000, "single") == pytest.approx(1_000, abs=0.01)

    def test_midway_between_thresholds(self):
        # other_income=25000, ss=10000 → provisional = 25000 + 5000 = 30000
        # excess over 25000 = 5000; 50% of excess = 2500
        # 50% of benefit = 5000
        # taxable = min(2500, 5000) = 2500
        assert compute_ss_taxation(10_000, 25_000, "single") == pytest.approx(2_500, abs=0.01)

    def test_at_upper_threshold(self):
        # other_income=29000, ss=10000 → provisional = 29000 + 5000 = 34000
        # excess over 25000 = 9000; 50% of excess = 4500
        # 50% of benefit = 5000
        # taxable = min(4500, 5000) = 4500
        assert compute_ss_taxation(10_000, 29_000, "single") == pytest.approx(4_500, abs=0.01)


# ---------------------------------------------------------------------------
# Single filer — above upper threshold ($34k)
# ---------------------------------------------------------------------------

class TestSSSingleAboveUpperThreshold:
    """Provisional > $34,000 → min(50% of first $9k + 85% of excess over $34k, 85% of benefit)."""

    def test_just_above_upper_threshold(self):
        # other_income=30000, ss=10000 → provisional = 30000 + 5000 = 35000
        # 50% of first $9000 (gap 25k–34k) = 4500
        # 85% of excess over 34000 = 0.85 * 1000 = 850
        # total = 4500 + 850 = 5350
        # 85% of benefit = 8500
        # taxable = min(5350, 8500) = 5350
        assert compute_ss_taxation(10_000, 30_000, "single") == pytest.approx(5_350, abs=0.01)

    def test_high_income_capped_at_85_percent(self):
        # other_income=80000, ss=20000 → provisional = 80000 + 10000 = 90000
        # 50% of $9000 = 4500
        # 85% of (90000 - 34000) = 0.85 * 56000 = 47600
        # total = 4500 + 47600 = 52100
        # 85% of benefit = 0.85 * 20000 = 17000
        # taxable = min(52100, 17000) = 17000 (capped)
        assert compute_ss_taxation(20_000, 80_000, "single") == pytest.approx(17_000, abs=0.01)

    def test_very_high_income_single(self):
        # other_income=200000, ss=30000 → provisional = 200000 + 15000 = 215000
        # Formula gives huge number, but capped at 85% of 30000 = 25500
        assert compute_ss_taxation(30_000, 200_000, "single") == pytest.approx(25_500, abs=0.01)


# ---------------------------------------------------------------------------
# Married filing jointly — below lower threshold ($32k)
# ---------------------------------------------------------------------------

class TestSSMFJBelowThreshold:
    """Provisional income < $32,000 → 0% taxable for MFJ."""

    def test_below_threshold(self):
        # other_income=20000, ss=20000 → provisional = 20000 + 10000 = 30000 < 32000
        assert compute_ss_taxation(20_000, 20_000, "married_joint") == 0.0

    def test_exactly_at_threshold(self):
        # other_income=22000, ss=20000 → provisional = 22000 + 10000 = 32000
        assert compute_ss_taxation(20_000, 22_000, "married_joint") == 0.0


# ---------------------------------------------------------------------------
# Married filing jointly — between thresholds ($32k–$44k)
# ---------------------------------------------------------------------------

class TestSSMFJBetweenThresholds:
    """$32,000 < provisional <= $44,000 → min(50% of excess, 50% of benefit)."""

    def test_between_thresholds(self):
        # other_income=30000, ss=20000 → provisional = 30000 + 10000 = 40000
        # excess over 32000 = 8000; 50% of excess = 4000
        # 50% of benefit = 10000
        # taxable = min(4000, 10000) = 4000
        assert compute_ss_taxation(20_000, 30_000, "married_joint") == pytest.approx(4_000, abs=0.01)


# ---------------------------------------------------------------------------
# Married filing jointly — above upper threshold ($44k)
# ---------------------------------------------------------------------------

class TestSSMFJAboveUpperThreshold:
    """Provisional > $44,000 → min(50% of first $12k + 85% of excess over $44k, 85% of benefit)."""

    def test_above_upper_threshold(self):
        # other_income=50000, ss=24000 → provisional = 50000 + 12000 = 62000
        # 50% of first $12000 (gap 32k–44k) = 6000
        # 85% of (62000 - 44000) = 0.85 * 18000 = 15300
        # total = 6000 + 15300 = 21300
        # 85% of benefit = 0.85 * 24000 = 20400
        # taxable = min(21300, 20400) = 20400 (capped)
        assert compute_ss_taxation(24_000, 50_000, "married_joint") == pytest.approx(20_400, abs=0.01)

    def test_high_income_mfj(self):
        # other_income=150000, ss=30000 → provisional = 150000 + 15000 = 165000
        # 85% of benefit = 25500 — will be capped
        assert compute_ss_taxation(30_000, 150_000, "married_joint") == pytest.approx(25_500, abs=0.01)


# ---------------------------------------------------------------------------
# Head of household — uses single thresholds
# ---------------------------------------------------------------------------

class TestSSHeadOfHousehold:
    """Head of household uses the same thresholds as single ($25k/$34k)."""

    def test_below_threshold(self):
        assert compute_ss_taxation(10_000, 15_000, "head_of_household") == 0.0

    def test_between_thresholds(self):
        # Same calc as single: other=22000, ss=10000 → provisional=27000
        # excess = 2000, 50% = 1000
        assert compute_ss_taxation(10_000, 22_000, "head_of_household") == pytest.approx(1_000, abs=0.01)

    def test_above_upper_threshold(self):
        # other=80000, ss=20000 → provisional=90000, capped at 85% of 20000 = 17000
        assert compute_ss_taxation(20_000, 80_000, "head_of_household") == pytest.approx(17_000, abs=0.01)


# ---------------------------------------------------------------------------
# Married filing separately — special rule: always 85% taxable
# ---------------------------------------------------------------------------

class TestSSMarriedSeparate:
    """Married filing separately: taxable = 85% of SS benefit (always)."""

    def test_low_income(self):
        assert compute_ss_taxation(10_000, 5_000, "married_separate") == pytest.approx(8_500, abs=0.01)

    def test_high_income(self):
        assert compute_ss_taxation(30_000, 200_000, "married_separate") == pytest.approx(25_500, abs=0.01)

    def test_zero_other_income(self):
        # Even with zero other income, married_separate is 85% taxable
        assert compute_ss_taxation(20_000, 0, "married_separate") == pytest.approx(17_000, abs=0.01)

    def test_zero_ss_still_zero(self):
        # Zero SS benefit → zero taxable, even for married_separate
        assert compute_ss_taxation(0, 100_000, "married_separate") == 0.0


# ---------------------------------------------------------------------------
# Benefit cap — taxable portion never exceeds 85% of benefit
# ---------------------------------------------------------------------------

class TestSSBenefitCap:
    """The taxable portion of SS can never exceed 85% of the total benefit."""

    def test_single_cap(self):
        taxable = compute_ss_taxation(10_000, 500_000, "single")
        assert taxable <= 10_000 * 0.85 + 0.01

    def test_mfj_cap(self):
        taxable = compute_ss_taxation(40_000, 1_000_000, "married_joint")
        assert taxable <= 40_000 * 0.85 + 0.01

    def test_hoh_cap(self):
        taxable = compute_ss_taxation(25_000, 300_000, "head_of_household")
        assert taxable <= 25_000 * 0.85 + 0.01
