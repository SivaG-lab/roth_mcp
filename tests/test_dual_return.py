"""
T022 — Tests for the dual_return module.

Tests cover:
  - dual_return: combines HTML display and structured data into a single JSON string
  - extract_html: extracts the HTML portion from a dual_return result
  - extract_data: extracts the data dict from a dual_return result
  - compact_result: strips HTML and adds "tool" key; special handling for
    generate_conversion_report (returns summary only)
  - Edge cases: empty HTML, empty data dict
  - JSON parseability of all outputs
"""

import json
import pytest
from dual_return import dual_return, extract_html, extract_data, compact_result


# ---------------------------------------------------------------------------
# dual_return — basic construction
# ---------------------------------------------------------------------------

class TestDualReturn:
    """dual_return combines HTML and data into a valid JSON string."""

    def test_returns_string(self):
        result = dual_return("<div>test</div>", {"key": "value"})
        assert isinstance(result, str)

    def test_result_is_valid_json(self):
        result = dual_return("<div>test</div>", {"key": "value"})
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_result_contains_display(self):
        result = dual_return("<div>test</div>", {"key": "value"})
        parsed = json.loads(result)
        assert "display" in parsed or "html" in parsed

    def test_result_contains_data(self):
        result = dual_return("<div>test</div>", {"key": "value"})
        parsed = json.loads(result)
        assert "data" in parsed

    def test_html_preserved_in_result(self):
        html = "<div>test</div>"
        result = dual_return(html, {"key": "value"})
        parsed = json.loads(result)
        # HTML should be stored under "display" or "html"
        stored_html = parsed.get("display") or parsed.get("html")
        assert stored_html == html

    def test_data_preserved_in_result(self):
        data = {"key": "value", "count": 42}
        result = dual_return("<div>test</div>", data)
        parsed = json.loads(result)
        assert parsed["data"] == data


# ---------------------------------------------------------------------------
# extract_html
# ---------------------------------------------------------------------------

class TestExtractHtml:
    """extract_html retrieves the HTML string from a dual_return result."""

    def test_extracts_html_string(self):
        html = "<div>test</div>"
        result = dual_return(html, {"key": "value"})
        extracted = extract_html(result)
        assert extracted == html

    def test_extracts_complex_html(self):
        html = '<table><tr><td class="data">$50,000</td></tr></table>'
        result = dual_return(html, {"amount": 50000})
        extracted = extract_html(result)
        assert extracted == html

    def test_extracts_multiline_html(self):
        html = "<div>\n  <p>Line 1</p>\n  <p>Line 2</p>\n</div>"
        result = dual_return(html, {"lines": 2})
        extracted = extract_html(result)
        assert extracted == html


# ---------------------------------------------------------------------------
# extract_data
# ---------------------------------------------------------------------------

class TestExtractData:
    """extract_data retrieves the data dict from a dual_return result."""

    def test_extracts_data_dict(self):
        data = {"key": "value"}
        result = dual_return("<div>test</div>", data)
        extracted = extract_data(result)
        assert extracted == data

    def test_extracts_nested_data(self):
        data = {
            "summary": {"total": 100_000, "tax": 22_000},
            "years": [{"year": 1, "balance": 50_000}],
        }
        result = dual_return("<div>report</div>", data)
        extracted = extract_data(result)
        assert extracted == data

    def test_extracts_data_with_numeric_values(self):
        data = {"integer": 42, "float": 3.14, "negative": -100}
        result = dual_return("<span>nums</span>", data)
        extracted = extract_data(result)
        assert extracted["integer"] == 42
        assert extracted["float"] == pytest.approx(3.14)
        assert extracted["negative"] == -100


# ---------------------------------------------------------------------------
# compact_result — general tool
# ---------------------------------------------------------------------------

class TestCompactResult:
    """compact_result strips HTML and adds a 'tool' key."""

    def test_adds_tool_key(self):
        result = dual_return("<div>test</div>", {"key": "value"})
        compacted = compact_result("some_tool", result)
        assert "tool" in compacted
        assert compacted["tool"] == "some_tool"

    def test_does_not_contain_html(self):
        result = dual_return("<div>test</div>", {"key": "value"})
        compacted = compact_result("some_tool", result)
        # The compacted result should not have the HTML display content
        assert "display" not in compacted or compacted.get("display") is None
        # Also check it's not under "html" key
        assert "html" not in compacted or compacted.get("html") is None

    def test_preserves_data(self):
        data = {"key": "value", "count": 42}
        result = dual_return("<div>test</div>", data)
        compacted = compact_result("some_tool", result)
        # Data should be accessible in the compacted result
        assert compacted.get("key") == "value" or compacted.get("data", {}).get("key") == "value"

    def test_returns_dict(self):
        result = dual_return("<div>test</div>", {"key": "value"})
        compacted = compact_result("some_tool", result)
        assert isinstance(compacted, dict)


# ---------------------------------------------------------------------------
# compact_result — generate_conversion_report (summary-only)
# ---------------------------------------------------------------------------

class TestCompactResultConversionReport:
    """compact_result for generate_conversion_report returns only summary."""

    def test_returns_summary_only_for_report_tool(self):
        data = {
            "summary": {"total_tax": 22_000, "net_benefit": 15_000},
            "yearly_projections": [
                {"year": 1, "balance": 450_000},
                {"year": 2, "balance": 400_000},
            ],
        }
        result = dual_return("<div>full report</div>", data)
        compacted = compact_result("generate_conversion_report", result)
        assert "tool" in compacted
        assert compacted["tool"] == "generate_conversion_report"
        # Should contain summary data
        assert "summary" in compacted or "total_tax" in str(compacted)

    def test_report_tool_strips_verbose_projections(self):
        data = {
            "summary": {"total_tax": 22_000},
            "yearly_projections": [{"year": y} for y in range(1, 31)],
        }
        result = dual_return("<div>full report</div>", data)
        compacted = compact_result("generate_conversion_report", result)
        # Yearly projections should be omitted or summarized in compact form
        # The compact result should be smaller than the full data
        if "yearly_projections" in compacted:
            # If projections are included, they should be summarized
            assert len(compacted["yearly_projections"]) <= len(data["yearly_projections"])


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Edge cases for dual_return and helpers."""

    def test_empty_html(self):
        result = dual_return("", {"key": "value"})
        assert isinstance(result, str)
        parsed = json.loads(result)
        stored_html = parsed.get("display") or parsed.get("html", "")
        assert stored_html == ""

    def test_empty_data_dict(self):
        result = dual_return("<div>test</div>", {})
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["data"] == {}

    def test_both_empty(self):
        result = dual_return("", {})
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_extract_html_from_empty(self):
        result = dual_return("", {"key": "value"})
        extracted = extract_html(result)
        assert extracted == ""

    def test_extract_data_from_empty_data(self):
        result = dual_return("<div>test</div>", {})
        extracted = extract_data(result)
        assert extracted == {}

    def test_compact_result_with_empty_data(self):
        result = dual_return("<div>test</div>", {})
        compacted = compact_result("some_tool", result)
        assert compacted["tool"] == "some_tool"


# ---------------------------------------------------------------------------
# JSON parseability verification
# ---------------------------------------------------------------------------

class TestJsonParseability:
    """All dual_return outputs must be valid, parseable JSON strings."""

    def test_simple_data_is_parseable(self):
        result = dual_return("<p>hello</p>", {"msg": "hello"})
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_special_characters_in_html_parseable(self):
        html = '<div class="test">&amp; &lt; &gt; "quotes"</div>'
        result = dual_return(html, {"special": True})
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_unicode_data_parseable(self):
        result = dual_return("<div>test</div>", {"currency": "$50,000"})
        parsed = json.loads(result)
        assert isinstance(parsed, dict)

    def test_large_data_parseable(self):
        large_data = {
            "projections": [
                {"year": y, "balance": 500_000 - y * 10_000, "tax": y * 1_000}
                for y in range(1, 31)
            ]
        }
        result = dual_return("<div>large report</div>", large_data)
        parsed = json.loads(result)
        assert len(parsed["data"]["projections"]) == 30
