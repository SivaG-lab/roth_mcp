"""
T010 — Tests for IRMAA (Income-Related Monthly Adjustment Amount) surcharge.

Tests cover:
  - All 6 tiers for single and married_joint filing statuses
  - Boundary values (just below, exactly at, just above each threshold)
  - married_separate and head_of_household use single thresholds
  - Monthly surcharge × 12 = annual surcharge
  - Zero / below-threshold cases

IRMAA thresholds (2024):
  single:        [(103000, 0), (129000, 65.90), (161000, 164.80),
                  (193000, 263.70), (500000, 362.60), (inf, 395.60)]
  married_joint: [(206000, 0), (258000, 65.90), (322000, 164.80),
                  (386000, 263.70), (750000, 362.60), (inf, 395.60)]

Surcharge values are MONTHLY Part B amounts; annual = monthly × 12.
"""

import math
import pytest
from tax.irmaa import compute_irmaa_surcharge


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def annual(monthly: float) -> float:
    """Convert monthly surcharge to annual."""
    return monthly * 12


# ---------------------------------------------------------------------------
# Single filer — tier-by-tier
# ---------------------------------------------------------------------------

class TestIrmaaSingle:
    """IRMAA surcharge for single filers."""

    def test_below_first_threshold(self):
        # MAGI $90,000 — well below $103k → $0
        assert compute_irmaa_surcharge(90_000, "single") == 0.0

    def test_exactly_at_first_threshold(self):
        # MAGI $103,000 — at boundary → $0 (tier 1 = no surcharge)
        assert compute_irmaa_surcharge(103_000, "single") == 0.0

    def test_just_above_first_threshold(self):
        # MAGI $103,001 → tier 2: $65.90/mo
        assert compute_irmaa_surcharge(103_001, "single") == pytest.approx(annual(65.90), abs=0.01)

    def test_tier2_mid_range(self):
        # MAGI $120,000 → tier 2: $65.90/mo
        assert compute_irmaa_surcharge(120_000, "single") == pytest.approx(annual(65.90), abs=0.01)

    def test_at_129k_boundary(self):
        # MAGI $129,000 — boundary between tier 2 and tier 3
        # At the boundary should still be tier 2
        assert compute_irmaa_surcharge(129_000, "single") == pytest.approx(annual(65.90), abs=0.01)

    def test_just_above_129k(self):
        # MAGI $129,001 → tier 3: $164.80/mo
        assert compute_irmaa_surcharge(129_001, "single") == pytest.approx(annual(164.80), abs=0.01)

    def test_tier3_at_161k(self):
        # MAGI $161,000 — boundary of tier 3/4
        assert compute_irmaa_surcharge(161_000, "single") == pytest.approx(annual(164.80), abs=0.01)

    def test_tier4(self):
        # MAGI $175,000 → tier 4: $263.70/mo
        assert compute_irmaa_surcharge(175_000, "single") == pytest.approx(annual(263.70), abs=0.01)

    def test_tier5(self):
        # MAGI $250,000 → tier 5: $362.60/mo
        assert compute_irmaa_surcharge(250_000, "single") == pytest.approx(annual(362.60), abs=0.01)

    def test_above_500k_max_tier(self):
        # MAGI $600,000 → tier 6 (max): $395.60/mo
        assert compute_irmaa_surcharge(600_000, "single") == pytest.approx(annual(395.60), abs=0.01)

    def test_very_high_income(self):
        # MAGI $2,000,000 → still tier 6 max
        assert compute_irmaa_surcharge(2_000_000, "single") == pytest.approx(annual(395.60), abs=0.01)


# ---------------------------------------------------------------------------
# Married filing jointly — tier-by-tier
# ---------------------------------------------------------------------------

class TestIrmaaMFJ:
    """IRMAA surcharge for married filing jointly."""

    def test_below_threshold(self):
        assert compute_irmaa_surcharge(200_000, "married_joint") == 0.0

    def test_at_206k_boundary(self):
        assert compute_irmaa_surcharge(206_000, "married_joint") == 0.0

    def test_just_above_206k(self):
        assert compute_irmaa_surcharge(206_001, "married_joint") == pytest.approx(annual(65.90), abs=0.01)

    def test_tier2_mid(self):
        assert compute_irmaa_surcharge(240_000, "married_joint") == pytest.approx(annual(65.90), abs=0.01)

    def test_at_258k_boundary(self):
        assert compute_irmaa_surcharge(258_000, "married_joint") == pytest.approx(annual(65.90), abs=0.01)

    def test_tier3(self):
        assert compute_irmaa_surcharge(300_000, "married_joint") == pytest.approx(annual(164.80), abs=0.01)

    def test_tier4(self):
        assert compute_irmaa_surcharge(350_000, "married_joint") == pytest.approx(annual(263.70), abs=0.01)

    def test_tier5(self):
        assert compute_irmaa_surcharge(500_000, "married_joint") == pytest.approx(annual(362.60), abs=0.01)

    def test_max_tier(self):
        assert compute_irmaa_surcharge(800_000, "married_joint") == pytest.approx(annual(395.60), abs=0.01)


# ---------------------------------------------------------------------------
# Married separate — uses single thresholds
# ---------------------------------------------------------------------------

class TestIrmaaMarriedSeparate:
    """Married filing separately uses the same thresholds as single."""

    def test_below_threshold(self):
        assert compute_irmaa_surcharge(90_000, "married_separate") == 0.0

    def test_above_first_threshold(self):
        assert compute_irmaa_surcharge(110_000, "married_separate") == pytest.approx(annual(65.90), abs=0.01)

    def test_max_tier(self):
        assert compute_irmaa_surcharge(600_000, "married_separate") == pytest.approx(annual(395.60), abs=0.01)


# ---------------------------------------------------------------------------
# Head of household — uses single thresholds
# ---------------------------------------------------------------------------

class TestIrmaaHeadOfHousehold:
    """Head of household uses the same thresholds as single."""

    def test_below_threshold(self):
        assert compute_irmaa_surcharge(90_000, "head_of_household") == 0.0

    def test_above_first_threshold(self):
        assert compute_irmaa_surcharge(110_000, "head_of_household") == pytest.approx(annual(65.90), abs=0.01)

    def test_max_tier(self):
        assert compute_irmaa_surcharge(600_000, "head_of_household") == pytest.approx(annual(395.60), abs=0.01)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestIrmaaEdgeCases:
    """Edge cases and input validation."""

    def test_zero_magi(self):
        assert compute_irmaa_surcharge(0, "single") == 0.0

    def test_negative_magi(self):
        assert compute_irmaa_surcharge(-50_000, "single") == 0.0

    def test_surcharge_is_annual_not_monthly(self):
        """The function must return the ANNUAL surcharge (monthly × 12)."""
        surcharge = compute_irmaa_surcharge(120_000, "single")
        # Monthly is $65.90, annual should be $790.80
        assert surcharge == pytest.approx(790.80, abs=0.01)
