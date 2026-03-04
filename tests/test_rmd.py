"""
T011 — Tests for Required Minimum Distribution (RMD) calculation.

Tests cover:
  - RMD for ages 73-90 using the Uniform Lifetime Table
  - Age < 73 returns zero (RMDs not required yet)
  - Zero IRA balance returns zero
  - Formula: rmd = ira_balance / distribution_period
  - Specific hand-calculated values

Uniform Lifetime Table (partial):
  73: 26.5, 74: 25.5, 75: 24.6, 76: 23.7, 77: 22.9, 78: 22.0,
  79: 21.1, 80: 20.2, 81: 19.4, 82: 18.5, 83: 17.7, 84: 16.8,
  85: 16.0, 86: 15.2, 87: 14.4, 88: 13.7, 89: 12.9, 90: 12.2
"""

import pytest
from tax.rmd import compute_rmd


# ---------------------------------------------------------------------------
# Uniform Lifetime Table verification
# ---------------------------------------------------------------------------

# Expected distribution periods from the IRS Uniform Lifetime Table
EXPECTED_PERIODS = {
    73: 26.5,
    74: 25.5,
    75: 24.6,
    76: 23.7,
    77: 22.9,
    78: 22.0,
    79: 21.1,
    80: 20.2,
    81: 19.4,
    82: 18.5,
    83: 17.7,
    84: 16.8,
    85: 16.0,
    86: 15.2,
    87: 14.4,
    88: 13.7,
    89: 12.9,
    90: 12.2,
}


class TestRmdBasicCalculation:
    """Core RMD formula: balance / distribution_period."""

    def test_age_73_500k_balance(self):
        """Canonical example: age 73, $500k → 500000 / 26.5 = 18867.92..."""
        rmd = compute_rmd(73, 500_000)
        expected = 500_000 / 26.5
        assert rmd == pytest.approx(expected, abs=0.01)

    def test_age_75_1m_balance(self):
        rmd = compute_rmd(75, 1_000_000)
        expected = 1_000_000 / 24.6
        assert rmd == pytest.approx(expected, abs=0.01)

    def test_age_80_750k_balance(self):
        rmd = compute_rmd(80, 750_000)
        expected = 750_000 / 20.2
        assert rmd == pytest.approx(expected, abs=0.01)

    def test_age_85_300k_balance(self):
        rmd = compute_rmd(85, 300_000)
        expected = 300_000 / 16.0
        assert rmd == pytest.approx(expected, abs=0.01)

    def test_age_90_200k_balance(self):
        rmd = compute_rmd(90, 200_000)
        expected = 200_000 / 12.2
        assert rmd == pytest.approx(expected, abs=0.01)


class TestRmdAllAges:
    """Parametrized test across all documented ages (73-90)."""

    @pytest.mark.parametrize("age,period", list(EXPECTED_PERIODS.items()))
    def test_rmd_for_age(self, age, period):
        balance = 1_000_000
        expected = balance / period
        rmd = compute_rmd(age, balance)
        assert rmd == pytest.approx(expected, abs=0.01), (
            f"age={age}, period={period}, expected={expected:.2f}, got={rmd:.2f}"
        )


# ---------------------------------------------------------------------------
# Below RMD age — should return zero
# ---------------------------------------------------------------------------

class TestRmdBelowAge:
    """Before age 73, no RMD is required."""

    def test_age_72(self):
        assert compute_rmd(72, 500_000) == 0.0

    def test_age_65(self):
        assert compute_rmd(65, 1_000_000) == 0.0

    def test_age_50(self):
        assert compute_rmd(50, 2_000_000) == 0.0

    def test_age_0(self):
        assert compute_rmd(0, 100_000) == 0.0


# ---------------------------------------------------------------------------
# Zero and edge-case balances
# ---------------------------------------------------------------------------

class TestRmdZeroBalance:
    """Zero IRA balance means zero RMD regardless of age."""

    def test_zero_balance_age_73(self):
        assert compute_rmd(73, 0) == 0.0

    def test_zero_balance_age_85(self):
        assert compute_rmd(85, 0) == 0.0

    def test_small_balance(self):
        """Very small balance should still compute correctly."""
        rmd = compute_rmd(73, 100)
        expected = 100 / 26.5
        assert rmd == pytest.approx(expected, abs=0.01)


# ---------------------------------------------------------------------------
# Large balances
# ---------------------------------------------------------------------------

class TestRmdLargeBalances:
    """Ensure no overflow or precision issues with large balances."""

    def test_10m_balance(self):
        rmd = compute_rmd(73, 10_000_000)
        expected = 10_000_000 / 26.5
        assert rmd == pytest.approx(expected, abs=0.01)

    def test_50m_balance(self):
        rmd = compute_rmd(80, 50_000_000)
        expected = 50_000_000 / 20.2
        assert rmd == pytest.approx(expected, abs=0.01)
