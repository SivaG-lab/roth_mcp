"""Inline CSS constants for HTML templates — color scheme per tool."""

# Tool colors
VALIDATION_GREEN = "#22c55e"
TAX_RED = "#ef4444"
PROJECTION_BLUE = "#3b82f6"
OPTIMIZATION_PURPLE = "#8b5cf6"
BREAKEVEN_BLUE = "#3b82f6"
REPORT_DARK = "#1e293b"

# Typography
FONT_FAMILY = "system-ui, -apple-system, sans-serif"
FONT_SIZE_BASE = "14px"
FONT_SIZE_HEADING = "1.1em"
FONT_SIZE_SMALL = "0.85em"

# Spacing
CARD_PADDING = "16px"
CARD_RADIUS = "8px"
CARD_MARGIN = "8px 0"
TABLE_CELL_PADDING = "4px 8px"

# Shared card wrapper
def card_style(color: str) -> str:
    return (
        f"border:2px solid {color};border-radius:{CARD_RADIUS};"
        f"padding:{CARD_PADDING};margin:{CARD_MARGIN};"
        f"font-family:{FONT_FAMILY};font-size:{FONT_SIZE_BASE}"
    )

def heading_style(color: str) -> str:
    return f"color:{color};margin:0 0 8px;font-size:{FONT_SIZE_HEADING}"

TABLE_STYLE = "width:100%;border-collapse:collapse"
TD_STYLE = f"padding:{TABLE_CELL_PADDING}"
TD_RIGHT = f"padding:{TABLE_CELL_PADDING};text-align:right"
TR_BOLD = "font-weight:bold;border-top:2px solid #444"
MUTED = f"color:#999;font-size:{FONT_SIZE_SMALL}"
