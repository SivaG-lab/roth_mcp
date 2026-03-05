# Kore.ai MCP Agent Setup Guide

## Prerequisites

- Python 3.10+
- roth_mcp server deployed and accessible via HTTP
- Kore.ai XO Platform account with MCP agent capability

## 1. Server Setup

### Install Core Dependencies

```bash
pip install -r requirements-core.txt
```

### Configure Environment

Create a `.env` file:

```env
MCP_TRANSPORT=sse
MCP_HOST=0.0.0.0
MCP_PORT=8080
RESPONSE_MODE=data_only
LOG_FORMAT=json
LOG_LEVEL=INFO
MCP_RATE_LIMIT=60
```

### Start the Server

```bash
python mcp_server.py
```

The server will listen on `http://0.0.0.0:8080`.

## 2. Kore.ai Configuration

### Add MCP Tool

1. Navigate to **Tools > Add Tool > +New Tool**
2. Set **Type**: SSE (or HTTP for streamable-http transport)
3. Set **URL**: `http://your-server:8080/sse` (SSE) or `http://your-server:8080/mcp` (HTTP)
4. Click **Test** — verify 7 tools are discovered
5. Select all tools and click **Add Selected**

### Parameter Configuration

For each tool, configure parameters as **Static** or **Dynamic**:

| Tool | Parameter | Config | Notes |
|------|-----------|--------|-------|
| validate_projection_inputs | current_age | Dynamic | Collect from user |
| validate_projection_inputs | retirement_age | Dynamic | Collect from user |
| validate_projection_inputs | filing_status | Dynamic | Dropdown (4 values) |
| validate_projection_inputs | state | Dynamic | Dropdown (51 values) |
| validate_projection_inputs | annual_income | Dynamic | Collect from user |
| validate_projection_inputs | trad_ira_balance | Dynamic | Collect from user |
| validate_projection_inputs | conversion_amount | Dynamic | Optional |
| validate_projection_inputs | annual_return | Static: 0.07 | Default assumption |
| validate_projection_inputs | model_years | Static: 30 | Default assumption |
| estimate_tax_components | annual_income | Dynamic | From prior context |
| estimate_tax_components | conversion_amount | Dynamic | From prior context |
| estimate_tax_components | filing_status | Dynamic | From prior context |
| estimate_tax_components | state | Dynamic | From prior context |
| analyze_roth_projections | trad_ira_balance | Dynamic | From prior context |
| analyze_roth_projections | current_age | Dynamic | From prior context |
| optimize_conversion_schedule | All 6 required | Dynamic | From prior context |
| breakeven_analysis | conversion_amount | Dynamic | From prior context |
| breakeven_analysis | current_age | Dynamic | From prior context |
| health_check | (none) | — | No parameters needed |

### Entity Rules

Configure entity extraction to automatically fill parameters from user messages:

| Entity | Type | Example Utterance |
|--------|------|-------------------|
| Age | Number | "I'm 55 years old" |
| Income | Currency | "I earn $120,000" |
| IRA Balance | Currency | "My IRA has $500,000" |
| State | Custom List | "I live in California" |
| Filing Status | Custom List | "I'm married filing jointly" |

### Answering Rules (Optional)

Add these rules to improve response quality:

1. **Always validate first**: "When a user provides financial information, always call validate_projection_inputs before other tools."
2. **Sequential workflow**: "After validation, estimate taxes, then run projections if the user wants long-term analysis."
3. **Report last**: "Only call generate_conversion_report after at least validation and tax estimation are complete."

## 3. Conversation Starters

Configure these as suggested prompts:

- "I want to analyze a Roth IRA conversion"
- "How much tax would I pay on a $50,000 conversion?"
- "What's the optimal conversion strategy for my situation?"
- "Is a Roth conversion worth it for me?"
- "Check server health"

## 4. Follow-up Workflow

The typical conversation flow:

1. **User provides info** → Agent calls `validate_projection_inputs`
2. **Validation passes** → Agent calls `estimate_tax_components`
3. **User asks for projections** → Agent calls `analyze_roth_projections`
4. **User wants optimization** → Agent calls `optimize_conversion_schedule`
5. **User asks if worth it** → Agent calls `breakeven_analysis`
6. **User wants summary** → Agent calls `generate_conversion_report`

## 5. Troubleshooting

| Issue | Solution |
|-------|----------|
| Tools not discovered | Check server URL and transport type match |
| Forms not showing | Ensure parameters are set to Dynamic |
| Empty dropdowns | Verify filing_status/state have enum schemas |
| Rate limit errors | Increase MCP_RATE_LIMIT or set to 0 |
| Connection refused | Check MCP_HOST and MCP_PORT, ensure firewall allows |
| Slow responses | Check LOG_LEVEL isn't DEBUG in production |

## 6. Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| MCP_TRANSPORT | stdio | Transport protocol: stdio, sse, streamable-http |
| MCP_HOST | 0.0.0.0 | Bind address for HTTP/SSE |
| MCP_PORT | 8080 | Port for HTTP/SSE |
| RESPONSE_MODE | full | Response format: full (HTML+data) or data_only |
| MCP_RATE_LIMIT | 0 | Max requests per minute (0 = disabled) |
| LOG_FORMAT | text | Log format: text or json |
| LOG_LEVEL | WARNING | Python log level |
