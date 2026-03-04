"""State income tax rates — flat effective rates for all 50 states + DC."""

STATE_TAX_RATES = {
    "AL": 0.0500,
    "AK": 0.0,
    "AZ": 0.0259,
    "AR": 0.0440,
    "CA": 0.0930,
    "CO": 0.0440,
    "CT": 0.0699,
    "DE": 0.0660,
    "FL": 0.0,
    "GA": 0.0549,
    "HI": 0.1100,
    "ID": 0.0580,
    "IL": 0.0495,
    "IN": 0.0305,
    "IA": 0.0570,
    "KS": 0.0570,
    "KY": 0.0400,
    "LA": 0.0425,
    "ME": 0.0715,
    "MD": 0.0575,
    "MA": 0.0500,
    "MI": 0.0425,
    "MN": 0.0985,
    "MS": 0.0500,
    "MO": 0.0495,
    "MT": 0.0675,
    "NE": 0.0684,
    "NV": 0.0,
    "NH": 0.0,
    "NJ": 0.1075,
    "NM": 0.0590,
    "NY": 0.0882,
    "NC": 0.0450,
    "ND": 0.0195,
    "OH": 0.0399,
    "OK": 0.0475,
    "OR": 0.0990,
    "PA": 0.0307,
    "RI": 0.0599,
    "SC": 0.0640,
    "SD": 0.0,
    "TN": 0.0,
    "TX": 0.0,
    "UT": 0.0465,
    "VT": 0.0875,
    "VA": 0.0575,
    "WA": 0.0,
    "WV": 0.0500,
    "WI": 0.0765,
    "WY": 0.0,
    "DC": 0.1075,
}


def compute_state_tax(taxable_conversion: float, state: str) -> float:
    """Compute state income tax as a flat rate on the taxable conversion amount.

    Args:
        taxable_conversion: The amount subject to state income tax.
        state: Two-letter state abbreviation (e.g. 'CA', 'TX').

    Returns:
        State tax owed. Returns 0.0 if the state is not found.
    """
    if taxable_conversion <= 0:
        return 0.0
    rate = STATE_TAX_RATES.get(state.upper(), 0.0)
    return round(rate * taxable_conversion, 2)
