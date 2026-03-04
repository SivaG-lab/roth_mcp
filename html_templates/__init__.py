# HTML template sub-package — public API
from html_templates.templates import (
    format_validation_result,
    format_tax_estimate,
    format_projection_table,
    format_optimization_schedule,
    format_breakeven,
    format_report,
)

__all__ = [
    "format_validation_result",
    "format_tax_estimate",
    "format_projection_table",
    "format_optimization_schedule",
    "format_breakeven",
    "format_report",
]
