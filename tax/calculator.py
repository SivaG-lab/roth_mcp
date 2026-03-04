"""Main tax computation entry point — combines all tax sub-modules."""

from __future__ import annotations

from tax.brackets import (
    FEDERAL_BRACKETS,
    STANDARD_DEDUCTIONS,
    ADDITIONAL_DEDUCTION_MARRIED,
    ADDITIONAL_DEDUCTION_SINGLE,
    compute_federal_tax,
    get_marginal_rate,
)
from tax.state_rates import compute_state_tax
from tax.irmaa import compute_irmaa_surcharge
from tax.rmd import compute_rmd
from tax.ss import compute_ss_taxation


def compute_tax_components(
    annual_income: float,
    conversion_amount: float,
    filing_status: str,
    state: str,
    *,
    cost_basis: float = 0.0,
    social_security: float = 0.0,
    rmd: float = 0.0,
    current_age: int | None = None,
    other_ordinary_income: float = 0.0,
) -> dict:
    """Compute full tax breakdown for a Roth conversion.

    Applies standard deduction BEFORE federal brackets per IRS methodology.

    Args:
        annual_income: Gross ordinary income (wages, pensions, etc.)
        conversion_amount: Roth conversion amount for this year
        filing_status: One of FilingStatus values
        state: 2-letter US state code
        cost_basis: After-tax basis in traditional IRA (non-taxable portion)
        social_security: Annual SS benefit
        rmd: RMD amount (already included in income if applicable)
        current_age: Current age (for age-based deduction)
        other_ordinary_income: Additional ordinary income

    Returns:
        Dict matching TaxEstimate fields.
    """
    # Taxable portion of conversion (exclude cost basis)
    taxable_conversion = max(conversion_amount - cost_basis, 0.0)

    # Total gross income
    gross_income = annual_income + taxable_conversion + other_ordinary_income

    # Standard deduction (with age 65+ additional)
    std_deduction = STANDARD_DEDUCTIONS.get(filing_status, 0)
    if current_age is not None and current_age >= 65:
        if filing_status in ("married_joint", "married_separate"):
            std_deduction += ADDITIONAL_DEDUCTION_MARRIED
        else:
            std_deduction += ADDITIONAL_DEDUCTION_SINGLE

    # Taxable income after deduction
    taxable_income = max(gross_income - std_deduction, 0.0)

    # Income WITHOUT conversion (for bracket comparison)
    income_without_conversion = max(
        annual_income + other_ordinary_income - std_deduction, 0.0
    )

    # Federal tax on total income
    total_federal_tax = compute_federal_tax(taxable_income, filing_status)
    # Federal tax without conversion (to get marginal cost of conversion)
    base_federal_tax = compute_federal_tax(income_without_conversion, filing_status)
    federal_tax = round(total_federal_tax - base_federal_tax, 2)

    # State tax on the taxable conversion only
    state_tax = compute_state_tax(taxable_conversion, state)

    # IRMAA impact (based on MAGI including conversion, 2-year lookback)
    magi_with = gross_income
    magi_without = annual_income + other_ordinary_income
    irmaa_with = compute_irmaa_surcharge(magi_with, filing_status)
    irmaa_without = compute_irmaa_surcharge(magi_without, filing_status)
    irmaa_impact = round(irmaa_with - irmaa_without, 2)

    # Social Security taxation impact
    ss_taxable_with = compute_ss_taxation(social_security, gross_income, filing_status)
    ss_taxable_without = compute_ss_taxation(
        social_security, annual_income + other_ordinary_income, filing_status
    )
    ss_tax_impact = round(ss_taxable_with - ss_taxable_without, 2)

    # RMD tax at marginal rate
    rmd_tax = 0.0
    if rmd > 0:
        marginal = get_marginal_rate(taxable_income, filing_status)
        rmd_tax = round(rmd * marginal, 2)

    # Totals
    total_tax_cost = round(
        federal_tax + state_tax + irmaa_impact + ss_tax_impact + rmd_tax, 2
    )
    effective_rate = round(total_tax_cost / conversion_amount, 4) if conversion_amount > 0 else 0.0
    marginal_rate = get_marginal_rate(taxable_income, filing_status)

    # Bracket labels
    bracket_before = f"{int(get_marginal_rate(income_without_conversion, filing_status) * 100)}%"
    bracket_after = f"{int(marginal_rate * 100)}%"

    return {
        "federal_tax": federal_tax,
        "state_tax": state_tax,
        "irmaa_impact": irmaa_impact,
        "ss_tax_impact": ss_tax_impact,
        "rmd_tax": rmd_tax,
        "total_tax_cost": total_tax_cost,
        "effective_rate": effective_rate,
        "marginal_rate": marginal_rate,
        "bracket_before": bracket_before,
        "bracket_after": bracket_after,
        "conversion_amount": conversion_amount,
    }


def compute_bracket_boundaries(
    annual_income: float, filing_status: str
) -> list[dict]:
    """Compute remaining room in each bracket above current income.

    Used by the optimizer to determine how much can be converted
    before crossing into the next bracket.

    Args:
        annual_income: Taxable income (after deductions).
        filing_status: Filing status string.

    Returns:
        List of dicts with bracket info: rate, ceiling, room_remaining.
    """
    brackets = FEDERAL_BRACKETS.get(filing_status, [])
    boundaries = []
    prev_ceiling = 0.0

    for ceiling, rate in brackets:
        if ceiling == float("inf"):
            room = float("inf")
        else:
            room = max(ceiling - max(annual_income, prev_ceiling), 0.0)
        boundaries.append({
            "rate": rate,
            "rate_label": f"{int(rate * 100)}%",
            "ceiling": ceiling,
            "room_remaining": room,
        })
        prev_ceiling = ceiling
        if annual_income < prev_ceiling and ceiling != float("inf"):
            pass  # keep going to show all brackets

    return boundaries
