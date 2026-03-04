"""Social Security benefit taxation using the provisional income formula."""

from __future__ import annotations


def compute_ss_taxation(
    ss_benefit: float, other_income: float, filing_status: str
) -> float:
    """Compute the taxable portion of Social Security benefits.

    Uses the IRS provisional income formula to determine how much of
    a taxpayer's Social Security benefits are subject to income tax.

    Args:
        ss_benefit: Annual Social Security benefit amount.
        other_income: All other income (wages, pensions, investment income,
                      tax-exempt interest, etc.) excluding Social Security.
        filing_status: One of 'single', 'married_joint', 'married_separate',
                       'head_of_household'.

    Returns:
        The taxable portion of Social Security benefits (not the tax itself).
        Returns 0.0 if ss_benefit <= 0.
    """
    if ss_benefit <= 0:
        return 0.0

    # Married filing separately: special rule -- always 85% taxable
    if filing_status == "married_separate":
        return round(min(0.85 * ss_benefit, ss_benefit), 2)

    # Provisional income = other_income + 50% of SS benefits
    provisional = other_income + 0.5 * ss_benefit

    # Determine thresholds based on filing status
    if filing_status in ("single", "head_of_household"):
        lower_threshold = 25000.0
        upper_threshold = 34000.0
    elif filing_status == "married_joint":
        lower_threshold = 32000.0
        upper_threshold = 44000.0
    else:
        raise ValueError(
            f"Unknown filing status: {filing_status!r}. "
            f"Must be one of 'single', 'married_joint', 'married_separate', "
            f"'head_of_household'"
        )

    # Below lower threshold: nothing is taxable
    if provisional <= lower_threshold:
        return 0.0

    # Between lower and upper threshold: up to 50% taxable
    if provisional <= upper_threshold:
        taxable = min(
            0.50 * (provisional - lower_threshold),
            0.50 * ss_benefit,
        )
        return round(taxable, 2)

    # Above upper threshold: up to 85% taxable
    taxable = min(
        0.50 * (upper_threshold - lower_threshold)
        + 0.85 * (provisional - upper_threshold),
        0.85 * ss_benefit,
    )
    return round(taxable, 2)
