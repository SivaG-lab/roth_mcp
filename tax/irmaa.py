"""IRMAA (Income-Related Monthly Adjustment Amount) surcharge lookup.

Medicare Part B premium surcharges based on MAGI, with 6 tiers for
single and married-filing-jointly filers.
"""

IRMAA_THRESHOLDS = {
    "single": [
        (103000, 0),
        (129000, 65.90),
        (161000, 164.80),
        (193000, 263.70),
        (500000, 362.60),
        (float("inf"), 395.60),
    ],
    "married_joint": [
        (206000, 0),
        (258000, 65.90),
        (322000, 164.80),
        (386000, 263.70),
        (750000, 362.60),
        (float("inf"), 395.60),
    ],
}


def compute_irmaa_surcharge(magi: float, filing_status: str) -> float:
    """Compute annual IRMAA surcharge based on MAGI and filing status.

    Args:
        magi: Modified Adjusted Gross Income.
        filing_status: One of 'single', 'married_joint', 'married_separate',
                       'head_of_household'.

    Returns:
        Annual IRMAA surcharge (monthly surcharge * 12).
    """
    # married_separate and head_of_household use the single thresholds
    if filing_status in ("married_separate", "head_of_household"):
        lookup_status = "single"
    else:
        lookup_status = filing_status

    thresholds = IRMAA_THRESHOLDS.get(lookup_status)
    if thresholds is None:
        raise ValueError(
            f"Unknown filing status: {filing_status!r}. "
            f"Must be one of 'single', 'married_joint', 'married_separate', "
            f"'head_of_household'"
        )

    for threshold, monthly_surcharge in thresholds:
        if magi <= threshold:
            return round(monthly_surcharge * 12, 2)

    # Should never reach here since the last threshold is inf,
    # but return top tier as a safety fallback.
    return round(thresholds[-1][1] * 12, 2)
