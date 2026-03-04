# Roth Conversion Calculator — MCP Server v2.0

A two-component Roth IRA conversion analysis system:

1. **FastMCP Server** — 6 financial analysis tools exposed via MCP stdio transport
2. **Streamlit Chat Agent** — GPT-4o-mini orchestrated chat UI that acts as MCP client

The system uses a Hybrid Orchestrator-Pipeline pattern: GPT handles conversation (input collection + summary), while a deterministic pipeline runs the 6 analysis tools sequentially and in parallel without extra GPT round-trips.

## Features

- **Federal + State tax calculation** with 2024 IRS brackets for all 50 states
- **IRMAA surcharge** estimation (Medicare Part B/D impact)
- **RMD projections** using IRS Uniform Lifetime Table
- **Social Security taxation** modeling
- **Multi-year conversion optimization** via bracket-filling strategy
- **Breakeven analysis** comparing convert vs. no-convert paths
- **Interactive HTML report** with downloadable output

## Prerequisites

- Python 3.10+
- OpenAI API key (GPT-4o-mini recommended for cost efficiency)

## Setup

```bash
cd roth_mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate    # Linux/macOS
# .venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-your-key-here
```

## Usage

```bash
# Start the Streamlit chat agent (spawns MCP server automatically)
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501`. Enter a message like:

> I'm 55 years old, married filing jointly, making $150k/year in California with a $500k Traditional IRA. I want to convert $50k per year for 5 years.

The system will:
1. Validate inputs and apply smart defaults
2. Calculate federal + state + IRMAA + SS tax impact
3. Run year-by-year projection, optimization, and breakeven analysis (in parallel)
4. Generate a comprehensive HTML report

### MCP Server Standalone

```bash
python mcp_server.py
# Server listens on stdio — connect with any MCP client
```

## Architecture

```
User ←→ Streamlit UI ←→ GPT Agent Loop ←→ MCP Client ←→ FastMCP Server
                              ↓
                     Deterministic Pipeline
                     ├── Stage 1: Tax Estimate (serial)
                     ├── Stage 2: Projections + Optimization + Breakeven (parallel)
                     └── Stage 3: Report Generation (serial)
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `validate_projection_inputs` | Validate and prepare all financial inputs |
| `estimate_tax_components` | Calculate federal, state, IRMAA, SS, RMD tax |
| `analyze_roth_projections` | Year-by-year convert vs. no-convert comparison |
| `optimize_conversion_schedule` | Find optimal multi-year schedule via bracket-filling |
| `breakeven_analysis` | Calculate years until conversion pays for itself |
| `generate_conversion_report` | Combine all results into HTML report |

All tools return dual-format JSON: `{"display": "<html>", "data": {...}}`

## Project Structure

```
roth_mcp/
├── mcp_server.py          # FastMCP server (6 tools)
├── streamlit_app.py       # Streamlit chat UI
├── agent_loop.py          # GPT conversation loop
├── pipeline.py            # Deterministic computation pipeline
├── mcp_client.py          # MCP session + ResilientToolExecutor
├── schema_converter.py    # MCP → OpenAI schema translation
├── models.py              # Dataclasses (UserProfile, TaxEstimate, etc.)
├── config.py              # Environment config (.env)
├── dual_return.py         # Dual-return envelope functions
├── validators.py          # Input validation (17+ fields)
├── prompts/system.md      # GPT system prompt
├── tax/                   # Tax computation modules
│   ├── brackets.py        # Federal tax brackets + standard deductions
│   ├── state_rates.py     # State income tax rates (all 50 states)
│   ├── calculator.py      # compute_tax_components() + bracket boundaries
│   ├── irmaa.py           # Medicare IRMAA surcharge tables
│   ├── rmd.py             # Required Minimum Distribution calculator
│   └── ss.py              # Social Security taxation logic
├── html_templates/        # HTML template formatters
│   ├── styles.py          # Shared CSS styles
│   └── templates.py       # 6 format_* functions for tool outputs
└── tests/                 # Unit + integration tests (305 tests)
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | *(required)* | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | GPT model for conversation |
| `OPENAI_TIMEOUT` | `30` | API timeout in seconds |
| `MAX_SESSION_COST` | `0.50` | Cost limit per session ($) |
| `MCP_SERVER_CMD` | `python` | Command to start MCP server |
| `MCP_SERVER_ARGS` | `mcp_server.py` | Server command arguments |

## Testing

```bash
pytest tests/ -v
```

305 tests covering: tax engine (116), validators (49), dual-return (38), tools (31), HTML templates (22), integration (8), orchestration (15), models (12), prompt eval (14).
