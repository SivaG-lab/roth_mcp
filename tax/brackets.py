"""2024 Federal tax brackets and standard deductions."""

from __future__ import annotations

FEDERAL_BRACKETS = {
    "single": [
        (11600, 0.10),
        (47150, 0.12),
        (100525, 0.22),
        (191950, 0.24),
        (243725, 0.32),
        (609350, 0.35),
        (float("inf"), 0.37),
    ],
    "married_joint": [
        (23200, 0.10),
        (94300, 0.12),
        (201050, 0.22),
        (383900, 0.24),
        (487450, 0.32),
        (731200, 0.35),
        (float("inf"), 0.37),
    ],
    "married_separate": [
        (11600, 0.10),
        (47150, 0.12),
        (100525, 0.22),
        (191950, 0.24),
        (243725, 0.32),
        (365600, 0.35),
        (float("inf"), 0.37),
    ],
    "head_of_household": [
        (16550, 0.10),
        (63100, 0.12),
        (100500, 0.22),
        (191950, 0.24),
        (243700, 0.32),
        (609350, 0.35),
        (float("inf"), 0.37),
    ],
}

STANDARD_DEDUCTIONS = {
    "single": 14600,
    "married_joint": 29200,
    "married_separate": 14600,
    "head_of_household": 21900,
}

ADDITIONAL_DEDUCTION_SINGLE = 1550  # age 65+
ADDITIONAL_DEDUCTION_MARRIED = 1300  # age 65+


def compute_federal_tax(taxable_income: float, filing_status: str) -> float:
    """Compute federal income tax using progressive bracket calculation.

    Args:
        taxable_income: Income after standard deduction has been applied.
        filing_status: One of 'single', 'married_joint', 'married_separate',
                       'head_of_household'.

    Returns:
        Total federal tax owed.
    """
    if taxable_income <= 0:
        return 0.0

    brackets = FEDERAL_BRACKETS.get(filing_status)
    if brackets is None:
        raise ValueError(
            f"Unknown filing status: {filing_status!r}. "
            f"Must be one of {list(FEDERAL_BRACKETS.keys())}"
        )

    tax = 0.0
    prev_ceiling = 0.0

    for ceiling, rate in brackets:
        if taxable_income <= prev_ceiling:
            break
        taxable_in_bracket = min(taxable_income, ceiling) - prev_ceiling
        tax += taxable_in_bracket * rate
        prev_ceiling = ceiling

    return round(tax, 2)


def get_marginal_rate(taxable_income: float, filing_status: str) -> float:
    """Return the marginal tax rate for a given taxable income.

    Args:
        taxable_income: Income after standard deduction has been applied.
        filing_status: One of 'single', 'married_joint', 'married_separate',
                       'head_of_household'.

    Returns:
        The marginal rate as a decimal (e.g. 0.22 for the 22% bracket).
        Returns 0.0 if taxable_income <= 0.
    """
    if taxable_income <= 0:
        return 0.0

    brackets = FEDERAL_BRACKETS.get(filing_status)
    if brackets is None:
        raise ValueError(
            f"Unknown filing status: {filing_status!r}. "
            f"Must be one of {list(FEDERAL_BRACKETS.keys())}"
        )

    for ceiling, rate in brackets:
        if taxable_income <= ceiling:
            return rate

    # Should never reach here since the last ceiling is inf,
    # but return top rate as a safety fallback.
    return brackets[-1][1]
