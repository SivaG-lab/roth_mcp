# Quickstart: Roth Conversion Calculator MCP Server v2.0

## Prerequisites

- Python 3.10+
- OpenAI API key (GPT-4o-mini recommended for cost)

## Setup

```bash
# Clone and enter project
cd roth_mcp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-your-key-here
```

## Run

```bash
# Start Streamlit chat agent (spawns MCP server automatically)
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501`. Type a message like:

> "I'm 55 years old, married filing jointly, making $150k/year in California with a $500k Traditional IRA. I want to convert $50k per year for 5 years."

The system will:
1. Validate your inputs and apply smart defaults
2. Calculate federal + state + IRMAA + SS tax impact
3. Run year-by-year projection, optimization, and breakeven analysis (in parallel)
4. Generate a comprehensive HTML report

## Test MCP Server Standalone

```bash
# Start MCP server directly (for development/debugging)
python mcp_server.py
# Server listens on stdio — connect with any MCP client
```

## Run Tests

```bash
pytest tests/ -v
```

## Project Structure

```
roth_mcp/
├── mcp_server.py          # FastMCP server (6 tools)
├── streamlit_app.py       # Chat UI entry point
├── agent_loop.py          # GPT conversation loop
├── pipeline.py            # Deterministic computation pipeline
├── mcp_client.py          # MCP session + ResilientToolExecutor
├── schema_converter.py    # MCP → OpenAI schema translation
├── models.py              # Dataclasses
├── config.py              # Environment config
├── dual_return.py         # Dual-return envelope functions
├── validators.py          # Input validation
├── prompts/system.md      # GPT system prompt
├── tax/                   # Tax computation modules
├── html/                  # HTML template formatters
└── tests/                 # Unit + integration tests
```

## Configuration (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| OPENAI_API_KEY | (required) | OpenAI API key |
| OPENAI_MODEL | gpt-4o-mini | GPT model to use |
| OPENAI_TIMEOUT | 30 | Seconds for OpenAI API calls |
| MAX_SESSION_COST | 0.50 | Cost limit per session ($) |
| MCP_SERVER_CMD | python | Command to start MCP server |
| MCP_SERVER_ARGS | mcp_server.py | Arguments for server command |
