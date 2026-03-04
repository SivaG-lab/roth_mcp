"""T032 — Tests for HTML template formatters.

Tests verify HTML structure, color coding, and content for each tool's formatter.
"""

import pytest
from html_templates import (
    format_validation_result,
    format_tax_estimate,
    format_projection_table,
    format_optimization_schedule,
    format_breakeven,
    format_report,
)
from html_templates.styles import (
    VALIDATION_GREEN, TAX_RED, PROJECTION_BLUE, OPTIMIZATION_PURPLE,
)


# ---------------------------------------------------------------------------
# format_validation_result
# ---------------------------------------------------------------------------

class TestFormatValidationResult:
    def test_complete_contains_green(self):
        result = {"status": "complete", "inputs": {"age": 55}, "auto_filled": {}, "missing": [], "errors": []}
        html = format_validation_result(result)
        assert VALIDATION_GREEN in html

    def test_complete_contains_checkmark(self):
        result = {"status": "complete", "inputs": {"age": 55}, "auto_filled": {}, "missing": [], "errors": []}
        html = format_validation_result(result)
        assert "Validated" in html

    def test_incomplete_contains_missing(self):
        result = {"status": "incomplete", "inputs": {}, "auto_filled": {}, "missing": ["current_age"], "errors": []}
        html = format_validation_result(result)
        assert "current_age" in html
        assert "Incomplete" in html

    def test_error_contains_error_messages(self):
        result = {"status": "error", "inputs": {}, "auto_filled": {}, "missing": [],
                  "errors": [{"field": "age", "message": "Too young"}]}
        html = format_validation_result(result)
        assert "Too young" in html
        assert TAX_RED in html

    def test_auto_filled_shown(self):
        result = {"status": "complete", "inputs": {"age": 55},
                  "auto_filled": {"rmd": {"value": 0, "reason": "Age < 73"}},
                  "missing": [], "errors": []}
        html = format_validation_result(result)
        assert "Age &lt; 73" in html


# ---------------------------------------------------------------------------
# format_tax_estimate
# ---------------------------------------------------------------------------

class TestFormatTaxEstimate:
    def test_contains_red_color(self):
        data = {"federal_tax": 5000, "state_tax": 2000, "irmaa_impact": 0,
                "ss_tax_impact": 0, "rmd_tax": 0, "total_tax_cost": 7000,
                "effective_rate": 0.14, "marginal_rate": 0.22,
                "bracket_before": "22%", "bracket_after": "24%",
                "conversion_amount": 50000}
        html = format_tax_estimate(data)
        assert TAX_RED in html

    def test_contains_table_rows(self):
        data = {"federal_tax": 5000, "state_tax": 2000, "irmaa_impact": 100,
                "ss_tax_impact": 50, "rmd_tax": 0, "total_tax_cost": 7150,
                "effective_rate": 0.143, "marginal_rate": 0.22,
                "bracket_before": "22%", "bracket_after": "24%",
                "conversion_amount": 50000}
        html = format_tax_estimate(data)
        assert "Federal Tax" in html
        assert "State Tax" in html
        assert "Total Tax Cost" in html

    def test_shows_conversion_amount(self):
        data = {"federal_tax": 0, "state_tax": 0, "irmaa_impact": 0,
                "ss_tax_impact": 0, "rmd_tax": 0, "total_tax_cost": 0,
                "effective_rate": 0, "marginal_rate": 0,
                "bracket_before": "", "bracket_after": "",
                "conversion_amount": 75000}
        html = format_tax_estimate(data)
        assert "75,000" in html


# ---------------------------------------------------------------------------
# format_projection_table
# ---------------------------------------------------------------------------

class TestFormatProjectionTable:
    def test_contains_blue_color(self):
        data = {"projections": [{"year": 1, "age": 56, "conversion": 50000,
                                 "roth_balance": 53500, "trad_balance": 450000,
                                 "tax_paid": 5000, "rmd_amount": 0}],
                "summary": {"final_roth_value": 53500, "final_trad_value": 450000,
                            "net_benefit": 3500, "crossover_year": 0}}
        html = format_projection_table(data)
        assert PROJECTION_BLUE in html

    def test_shows_5_year_summary(self):
        projections = [
            {"year": i, "age": 55 + i, "conversion": 50000,
             "roth_balance": 50000 * i, "trad_balance": 500000 - 50000 * i,
             "tax_paid": 5000, "rmd_amount": 0}
            for i in range(1, 11)
        ]
        data = {"projections": projections,
                "summary": {"final_roth_value": 500000, "final_trad_value": 0,
                            "net_benefit": 50000, "crossover_year": 5}}
        html = format_projection_table(data)
        assert "details" in html  # collapsible section
        assert "Show all 10 years" in html

    def test_net_benefit_shown(self):
        data = {"projections": [], "summary": {"final_roth_value": 0, "final_trad_value": 0,
                                                "net_benefit": 12345, "crossover_year": 0}}
        html = format_projection_table(data)
        assert "12,345" in html


# ---------------------------------------------------------------------------
# format_optimization_schedule
# ---------------------------------------------------------------------------

class TestFormatOptimizationSchedule:
    def test_contains_purple_color(self):
        data = {"optimal_schedule": [50000, 50000], "total_tax_cost": 10000,
                "tax_saved_vs_baseline": 5000, "converged": True, "confidence": 1.0}
        html = format_optimization_schedule(data)
        assert OPTIMIZATION_PURPLE in html

    def test_shows_nonzero_years(self):
        data = {"optimal_schedule": [50000, 30000, 0, 0], "total_tax_cost": 8000,
                "tax_saved_vs_baseline": 2000, "converged": True, "confidence": 1.0}
        html = format_optimization_schedule(data)
        assert "Year 1" in html
        assert "Year 2" in html

    def test_shows_convergence(self):
        data = {"optimal_schedule": [50000], "total_tax_cost": 5000,
                "tax_saved_vs_baseline": 1000, "converged": False, "confidence": 0.8}
        html = format_optimization_schedule(data)
        assert "No" in html
        assert "80%" in html


# ---------------------------------------------------------------------------
# format_breakeven
# ---------------------------------------------------------------------------

class TestFormatBreakeven:
    def test_contains_blue_color(self):
        data = {"breakeven_years": 8, "breakeven_age": 63, "assessment": "worth_it"}
        html = format_breakeven(data)
        assert "#3b82f6" in html  # BREAKEVEN_BLUE

    def test_worth_it_shown_green(self):
        data = {"breakeven_years": 5, "breakeven_age": 60, "assessment": "worth_it"}
        html = format_breakeven(data)
        assert "#22c55e" in html
        assert "Worth It" in html

    def test_marginal_shown_amber(self):
        data = {"breakeven_years": 15, "breakeven_age": 70, "assessment": "marginal"}
        html = format_breakeven(data)
        assert "#f59e0b" in html
        assert "Marginal" in html

    def test_not_worth_it_shown_red(self):
        data = {"breakeven_years": 25, "breakeven_age": 80, "assessment": "not_worth_it"}
        html = format_breakeven(data)
        assert "#ef4444" in html
        assert "Not Worth It" in html

    def test_shows_years_and_age(self):
        data = {"breakeven_years": 8, "breakeven_age": 63, "assessment": "worth_it"}
        html = format_breakeven(data)
        assert "8 years" in html
        assert "age 63" in html


# ---------------------------------------------------------------------------
# format_report
# ---------------------------------------------------------------------------

class TestFormatReport:
    def test_all_sections_present(self):
        inputs_data = {"inputs": {"current_age": 55, "state": "CA"}}
        tax_data = {"federal_tax": 5000, "state_tax": 2000, "total_tax_cost": 7000,
                    "effective_rate": 0.14, "marginal_rate": 0.22,
                    "bracket_before": "22%", "bracket_after": "24%",
                    "irmaa_impact": 0, "ss_tax_impact": 0, "rmd_tax": 0,
                    "conversion_amount": 50000}
        proj_data = {"projections": [{"year": 1, "age": 56, "conversion": 50000,
                                      "roth_balance": 50000, "trad_balance": 450000,
                                      "tax_paid": 5000, "rmd_amount": 0}],
                     "summary": {"final_roth_value": 50000, "final_trad_value": 450000,
                                 "net_benefit": 5000, "crossover_year": 0}}
        opt_data = {"optimal_schedule": [50000], "total_tax_cost": 5000,
                    "tax_saved_vs_baseline": 2000, "converged": True, "confidence": 1.0}
        be_data = {"breakeven_years": 8, "breakeven_age": 63, "assessment": "worth_it"}
        html = format_report(inputs_data, tax_data, proj_data, opt_data, be_data)
        assert "Input Summary" in html
        assert "Tax Estimate" in html
        assert "Projections" in html
        assert "Optimal" in html or "Schedule" in html
        assert "Breakeven" in html
        assert "disclaimer" in html.lower() or "educational" in html.lower()

    def test_handles_empty_sections(self):
        html = format_report({}, {}, {}, {}, {})
        assert "Report" in html
        assert "educational" in html.lower()

    def test_styled_with_colors(self):
        tax_data = {"federal_tax": 1000, "state_tax": 500, "total_tax_cost": 1500,
                    "effective_rate": 0.03, "marginal_rate": 0.12,
                    "bracket_before": "12%", "bracket_after": "12%",
                    "irmaa_impact": 0, "ss_tax_impact": 0, "rmd_tax": 0,
                    "conversion_amount": 50000}
        html = format_report({}, tax_data, {}, {}, {})
        assert TAX_RED in html
