"""Input validation for Roth Conversion Calculator.

Validates all 17+ user inputs, applies auto-fill defaults,
and returns structured result with status/inputs/assumptions/errors.
"""

from __future__ import annotations

from typing import Literal

from tax.state_rates import STATE_TAX_RATES

VALID_FILING_STATUSES = {"single", "married_joint", "married_separate", "head_of_household"}
VALID_STATES = set(STATE_TAX_RATES.keys())

FilingStatus = Literal["single", "married_joint", "married_separate", "head_of_household"]
StateCode = Literal[
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC",
]
REQUIRED_FIELDS = ["current_age", "retirement_age", "filing_status", "state", "annual_income", "trad_ira_balance"]


def validate_inputs(**kwargs) -> dict:
    """Validate all user financial inputs for Roth conversion analysis.

    Returns:
        Dict with keys: status, inputs, assumptions, auto_filled, missing, errors
    """
    errors = []
    missing = []
    auto_filled = {}
    inputs = {}
    assumptions = {}

    # --- Extract and validate individual fields ---

    # current_age
    current_age = kwargs.get("current_age")
    if current_age is not None:
        if not isinstance(current_age, (int, float)) or current_age != int(current_age):
            errors.append({"field": "current_age", "message": "Age must be an integer"})
        else:
            current_age = int(current_age)
            if current_age < 18 or current_age > 100:
                errors.append({"field": "current_age", "message": "Age must be between 18 and 100"})
            else:
                inputs["current_age"] = current_age
    else:
        missing.append("current_age")

    # retirement_age
    retirement_age = kwargs.get("retirement_age")
    if retirement_age is not None:
        if not isinstance(retirement_age, (int, float)) or retirement_age != int(retirement_age):
            errors.append({"field": "retirement_age", "message": "Retirement age must be an integer"})
        else:
            retirement_age = int(retirement_age)
            if retirement_age > 100:
                errors.append({"field": "retirement_age", "message": "Retirement age must be ≤ 100"})
            elif current_age is not None and isinstance(current_age, int) and retirement_age <= current_age:
                errors.append({"field": "retirement_age", "message": "Retirement age must be greater than current age"})
            else:
                inputs["retirement_age"] = retirement_age
    else:
        missing.append("retirement_age")

    # filing_status
    filing_status = kwargs.get("filing_status")
    if filing_status is not None:
        if filing_status not in VALID_FILING_STATUSES:
            errors.append({"field": "filing_status", "message": f"Filing status must be one of {sorted(VALID_FILING_STATUSES)}"})
        else:
            inputs["filing_status"] = filing_status
    else:
        missing.append("filing_status")

    # state
    state = kwargs.get("state")
    if state is not None:
        state_upper = state.upper() if isinstance(state, str) else state
        if state_upper not in VALID_STATES:
            errors.append({"field": "state", "message": f"Invalid state code: {state}"})
        else:
            inputs["state"] = state_upper
    else:
        missing.append("state")

    # annual_income
    annual_income = kwargs.get("annual_income")
    if annual_income is not None:
        if not isinstance(annual_income, (int, float)):
            errors.append({"field": "annual_income", "message": "Annual income must be a number"})
        elif annual_income < 0:
            errors.append({"field": "annual_income", "message": "Annual income must be ≥ 0"})
        else:
            inputs["annual_income"] = float(annual_income)
    else:
        missing.append("annual_income")

    # trad_ira_balance
    trad_ira_balance = kwargs.get("trad_ira_balance")
    if trad_ira_balance is not None:
        if not isinstance(trad_ira_balance, (int, float)):
            errors.append({"field": "trad_ira_balance", "message": "IRA balance must be a number"})
        elif trad_ira_balance < 0:
            errors.append({"field": "trad_ira_balance", "message": "IRA balance must be ≥ 0"})
        else:
            inputs["trad_ira_balance"] = float(trad_ira_balance)
    else:
        missing.append("trad_ira_balance")

    # --- Conversion amount / schedule ---
    conversion_amount = kwargs.get("conversion_amount")
    conversion_schedule = kwargs.get("conversion_schedule")

    if conversion_schedule is not None:
        # Schedule takes precedence
        if isinstance(conversion_schedule, list) and not conversion_schedule:
            errors.append({"field": "conversion_schedule", "message": "Conversion schedule must not be empty"})
        elif isinstance(conversion_schedule, list) and all(isinstance(x, (int, float)) for x in conversion_schedule):
            if len(conversion_schedule) > 50:
                errors.append({"field": "conversion_schedule", "message": "Schedule must have ≤ 50 entries"})
            elif any(x < 0 for x in conversion_schedule):
                errors.append({"field": "conversion_schedule", "message": "Schedule amounts must be ≥ 0"})
            elif trad_ira_balance is not None and sum(conversion_schedule) > trad_ira_balance:
                errors.append({"field": "conversion_schedule", "message": "Schedule total must be ≤ IRA balance"})
            else:
                inputs["conversion_schedule"] = [float(x) for x in conversion_schedule]
        else:
            errors.append({"field": "conversion_schedule", "message": "Conversion schedule must be a list of numbers"})
    elif conversion_amount is not None:
        if not isinstance(conversion_amount, (int, float)):
            errors.append({"field": "conversion_amount", "message": "Conversion amount must be a number"})
        elif conversion_amount <= 0:
            errors.append({"field": "conversion_amount", "message": "Conversion amount must be > 0"})
        elif trad_ira_balance is not None and conversion_amount > trad_ira_balance:
            errors.append({"field": "conversion_amount", "message": "Conversion amount must be ≤ IRA balance"})
        else:
            # Auto-wrap single amount to schedule
            inputs["conversion_schedule"] = [float(conversion_amount)]

    # --- Optional fields with defaults ---
    roth_initial = kwargs.get("roth_ira_balance_initial")
    if roth_initial is not None:
        inputs["roth_ira_balance_initial"] = float(roth_initial)
    else:
        inputs["roth_ira_balance_initial"] = 0.0

    cost_basis = kwargs.get("cost_basis")
    if cost_basis is not None:
        inputs["cost_basis"] = float(cost_basis)
    else:
        inputs["cost_basis"] = 0.0

    # --- Assumptions (with user overrides) ---
    annual_return = kwargs.get("annual_return")
    if annual_return is not None:
        if not isinstance(annual_return, (int, float)):
            errors.append({"field": "annual_return", "message": "Annual return must be a number"})
        elif annual_return <= -1 or annual_return > 0.30:
            errors.append({"field": "annual_return", "message": "Annual return must be > -1 and ≤ 0.30"})
        else:
            assumptions["annual_return"] = float(annual_return)
    else:
        assumptions["annual_return"] = 0.07

    model_years = kwargs.get("model_years")
    if model_years is not None:
        if not isinstance(model_years, (int, float)) or model_years != int(model_years):
            errors.append({"field": "model_years", "message": "Model years must be an integer"})
        else:
            model_years = int(model_years)
            if model_years < 1 or model_years > 50:
                errors.append({"field": "model_years", "message": "Model years must be between 1 and 50"})
            else:
                assumptions["model_years"] = model_years
    else:
        assumptions["model_years"] = 30

    # --- Auto-fill logic ---
    age_val = inputs.get("current_age")
    income_val = inputs.get("annual_income")
    fs_val = inputs.get("filing_status")

    # Social Security: default 0 if age < 62
    ss = kwargs.get("social_security")
    if ss is not None:
        inputs["social_security"] = float(ss)
    elif age_val is not None and age_val < 62:
        auto_filled["social_security"] = {
            "value": 0,
            "source": "age_based_default",
            "reason": "Age < 62",
        }
        inputs["social_security"] = 0.0
    else:
        inputs["social_security"] = 0.0

    # RMD: default 0 if age < 73
    rmd = kwargs.get("rmd")
    if rmd is not None:
        inputs["rmd"] = float(rmd)
    elif age_val is not None and age_val < 73:
        auto_filled["rmd"] = {
            "value": 0,
            "source": "age_based_default",
            "reason": "Age < 73",
        }
        inputs["rmd"] = 0.0
    else:
        inputs["rmd"] = 0.0

    # --- Determine status ---
    if errors:
        return {
            "status": "error",
            "inputs": inputs,
            "assumptions": assumptions,
            "auto_filled": auto_filled,
            "missing": missing,
            "errors": errors,
        }

    has_conversion = "conversion_schedule" in inputs
    if missing or not has_conversion:
        status = "incomplete"
    else:
        status = "complete"

    return {
        "status": status,
        "inputs": inputs,
        "assumptions": assumptions,
        "auto_filled": auto_filled,
        "missing": missing,
        "errors": errors,
    }
