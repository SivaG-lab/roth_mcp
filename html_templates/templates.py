"""HTML formatter functions — one per MCP tool, using inline CSS."""

from __future__ import annotations

import html as _html

from html_templates.styles import (
    VALIDATION_GREEN, TAX_RED, PROJECTION_BLUE, OPTIMIZATION_PURPLE,
    BREAKEVEN_BLUE, card_style, heading_style,
    TABLE_STYLE, TD_STYLE, TD_RIGHT, TR_BOLD, MUTED,
)


def format_validation_result(result: dict) -> str:
    """Green card for validated inputs."""
    status = result.get("status", "incomplete")
    if status == "complete":
        return _validation_complete(result)
    elif status == "error":
        return _validation_error(result)
    return _validation_incomplete(result)


def _validation_complete(result: dict) -> str:
    inputs = result.get("inputs", {})
    auto = result.get("auto_filled", {})
    rows = "".join(
        f"<tr><td style='{TD_STYLE}'>{_html.escape(str(k))}</td><td style='{TD_RIGHT}'>{_html.escape(_fmt_val(v))}</td></tr>"
        for k, v in inputs.items()
    )
    auto_rows = "".join(
        f"<tr><td style='{TD_STYLE}'>{_html.escape(str(k))}</td>"
        f"<td style='{TD_RIGHT}'>{_html.escape(str(v['value']))} ({_html.escape(str(v['reason']))})</td></tr>"
        for k, v in auto.items()
    )
    return (
        f"<div style='{card_style(VALIDATION_GREEN)}'>"
        f"<h3 style='{heading_style(VALIDATION_GREEN)}'>&#10003; Inputs Validated</h3>"
        f"<table style='{TABLE_STYLE}'>{rows}</table>"
        + (f"<h4 style='margin:8px 0 4px'>Auto-filled</h4>"
           f"<table style='{TABLE_STYLE}'>{auto_rows}</table>" if auto else "")
        + "</div>"
    )


def _validation_incomplete(result: dict) -> str:
    missing = ", ".join(_html.escape(str(m)) for m in result.get("missing", []))
    return (
        f"<div style='{card_style('#f59e0b')}'>"
        f"<h3 style='{heading_style('#f59e0b')}'>&#9888; Incomplete Inputs</h3>"
        f"<p>Missing: {missing}</p></div>"
    )


def _validation_error(result: dict) -> str:
    errs = "".join(
        f"<li>{_html.escape(str(e['field']))}: {_html.escape(str(e['message']))}</li>" for e in result.get("errors", [])
    )
    return (
        f"<div style='{card_style(TAX_RED)}'>"
        f"<h3 style='{heading_style(TAX_RED)}'>&#10007; Validation Errors</h3>"
        f"<ul>{errs}</ul></div>"
    )


def format_tax_estimate(result: dict) -> str:
    """Red card with tax breakdown table."""
    conv = result.get("conversion_amount", 0)
    return (
        f"<div style='{card_style(TAX_RED)}'>"
        f"<h3 style='{heading_style(TAX_RED)}'>Tax Estimate: ${conv:,.0f} Conversion</h3>"
        f"<table style='{TABLE_STYLE}'>"
        f"<tr><td style='{TD_STYLE}'>Federal Tax</td><td style='{TD_RIGHT}'>${result.get('federal_tax', 0):,.2f}</td></tr>"
        f"<tr><td style='{TD_STYLE}'>State Tax</td><td style='{TD_RIGHT}'>${result.get('state_tax', 0):,.2f}</td></tr>"
        f"<tr><td style='{TD_STYLE}'>IRMAA Impact</td><td style='{TD_RIGHT}'>${result.get('irmaa_impact', 0):,.2f}</td></tr>"
        f"<tr><td style='{TD_STYLE}'>SS Tax Impact</td><td style='{TD_RIGHT}'>${result.get('ss_tax_impact', 0):,.2f}</td></tr>"
        f"<tr><td style='{TD_STYLE}'>RMD Tax</td><td style='{TD_RIGHT}'>${result.get('rmd_tax', 0):,.2f}</td></tr>"
        f"<tr style='{TR_BOLD}'><td style='{TD_STYLE}'>Total Tax Cost</td>"
        f"<td style='{TD_RIGHT}'>${result.get('total_tax_cost', 0):,.2f}</td></tr>"
        f"</table>"
        f"<p style='{MUTED}'>Effective rate: {result.get('effective_rate', 0):.1%} | "
        f"Bracket: {_html.escape(str(result.get('bracket_before', '')))} &rarr; {_html.escape(str(result.get('bracket_after', '')))}</p></div>"
    )


def format_projection_table(data: dict) -> str:
    """Blue card with 5-year summary + collapsible full table."""
    projections = data.get("projections", [])
    summary = data.get("summary", {})

    rows_5yr = "".join(
        f"<tr><td style='{TD_STYLE}'>{p['year']}</td><td style='{TD_STYLE}'>{p['age']}</td>"
        f"<td style='{TD_RIGHT}'>${p['conversion']:,.0f}</td>"
        f"<td style='{TD_RIGHT}'>${p['roth_balance']:,.0f}</td>"
        f"<td style='{TD_RIGHT}'>${p['trad_balance']:,.0f}</td></tr>"
        for p in projections[:5]
    )

    all_rows = "".join(
        f"<tr><td style='{TD_STYLE}'>{p['year']}</td><td style='{TD_STYLE}'>{p['age']}</td>"
        f"<td style='{TD_RIGHT}'>${p['conversion']:,.0f}</td>"
        f"<td style='{TD_RIGHT}'>${p['roth_balance']:,.0f}</td>"
        f"<td style='{TD_RIGHT}'>${p['trad_balance']:,.0f}</td>"
        f"<td style='{TD_RIGHT}'>${p['tax_paid']:,.0f}</td></tr>"
        for p in projections
    )

    header_5 = "<tr><th>Year</th><th>Age</th><th>Convert</th><th>Roth</th><th>Trad</th></tr>"
    header_all = "<tr><th>Year</th><th>Age</th><th>Convert</th><th>Roth</th><th>Trad</th><th>Tax</th></tr>"

    return (
        f"<div style='{card_style(PROJECTION_BLUE)}'>"
        f"<h3 style='{heading_style(PROJECTION_BLUE)}'>Roth Conversion Projections</h3>"
        f"<p>Net benefit: ${summary.get('net_benefit', 0):,.0f} | "
        f"Crossover year: {summary.get('crossover_year', 'N/A') or 'N/A'}</p>"
        f"<table style='{TABLE_STYLE}'>{header_5}{rows_5yr}</table>"
        f"<details><summary>Show all {len(projections)} years</summary>"
        f"<table style='{TABLE_STYLE}'>{header_all}{all_rows}</table></details></div>"
    )


def format_optimization_schedule(data: dict) -> str:
    """Purple card with optimal schedule."""
    schedule = data.get("optimal_schedule", [])
    nonzero = [(i + 1, a) for i, a in enumerate(schedule) if a > 0]
    rows = "".join(
        f"<tr><td style='{TD_STYLE}'>Year {y}</td><td style='{TD_RIGHT}'>${a:,.0f}</td></tr>"
        for y, a in nonzero
    )
    total_tax = data.get("total_tax_cost", 0)
    saved = data.get("tax_saved_vs_baseline", 0)
    converged = data.get("converged", True)
    confidence = data.get("confidence", 1.0)

    return (
        f"<div style='{card_style(OPTIMIZATION_PURPLE)}'>"
        f"<h3 style='{heading_style(OPTIMIZATION_PURPLE)}'>Optimal Conversion Schedule</h3>"
        f"<table style='{TABLE_STYLE}'>{rows}</table>"
        f"<p>Total tax: ${total_tax:,.0f} | Saved vs lump-sum: ${saved:,.0f}</p>"
        f"<p>Converged: {'Yes' if converged else 'No'} | Confidence: {confidence:.0%}</p></div>"
    )


def format_breakeven(data: dict) -> str:
    """Blue card with breakeven analysis and assessment."""
    years = data.get("breakeven_years", 0)
    age = data.get("breakeven_age", 0)
    assessment = data.get("assessment", "")

    color_map = {"worth_it": "#22c55e", "marginal": "#f59e0b", "not_worth_it": "#ef4444"}
    label_map = {"worth_it": "Worth It", "marginal": "Marginal", "not_worth_it": "Not Worth It"}
    assess_color = color_map.get(assessment, "#999")
    assess_label = label_map.get(assessment, _html.escape(str(assessment)))

    return (
        f"<div style='{card_style(BREAKEVEN_BLUE)}'>"
        f"<h3 style='{heading_style(BREAKEVEN_BLUE)}'>Breakeven Analysis</h3>"
        f"<p>Breakeven in <strong>{years} years</strong> (age {age})</p>"
        f"<p style='color:{assess_color};font-weight:bold;font-size:1.2em'>"
        f"Assessment: {assess_label}</p></div>"
    )


def format_report(
    inputs_data: dict,
    tax_data: dict,
    proj_data: dict,
    opt_data: dict,
    be_data: dict,
) -> str:
    """Full styled report combining all sections."""
    parts = [
        "<div style='font-family:system-ui;max-width:800px;margin:0 auto;padding:20px'>"
        "<h1 style='color:#3b82f6;border-bottom:3px solid #3b82f6;padding-bottom:8px'>"
        "Roth Conversion Analysis Report</h1>"
        "<p style='color:#999'>Generated by Roth Conversion Calculator MCP v2.0</p>"
    ]

    # Input summary
    if inputs_data:
        user_inputs = inputs_data.get("inputs", inputs_data)
        rows = "".join(
            f"<tr><td style='{TD_STYLE}'>{_html.escape(str(k))}</td><td style='{TD_RIGHT}'>{_html.escape(str(v))}</td></tr>"
            for k, v in user_inputs.items()
        )
        parts.append(f"<h2>Input Summary</h2><table style='{TABLE_STYLE}'>{rows}</table>")

    # Tax
    if tax_data and "federal_tax" in tax_data:
        parts.append(format_tax_estimate(tax_data))

    # Projections
    if proj_data and "projections" in proj_data:
        parts.append(format_projection_table(proj_data))

    # Optimization
    if opt_data and "optimal_schedule" in opt_data:
        parts.append(format_optimization_schedule(opt_data))

    # Breakeven
    if be_data and "assessment" in be_data:
        parts.append(format_breakeven(be_data))

    # Disclaimer
    parts.append(
        "<hr style='margin:20px 0'>"
        "<p style='color:#999;font-size:0.85em'>"
        "&#9888; This analysis is for educational purposes only and does not constitute tax advice. "
        "Consult a qualified tax professional before making conversion decisions.</p>"
        "</div>"
    )

    return "\n".join(parts)


def _fmt_val(v) -> str:
    """Format a value for display in HTML table."""
    if isinstance(v, float):
        if abs(v) >= 1000:
            return f"${v:,.2f}"
        if 0 < abs(v) < 1:
            return f"{v:.1%}"
        return f"{v:,.2f}"
    if isinstance(v, list):
        return ", ".join(f"${x:,.0f}" for x in v) if v else "—"
    return str(v)
