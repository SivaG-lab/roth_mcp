---
name: prism-ade
description: "Prism Agentic Document Extraction system. Use when working on document extraction, PDF parsing, OCR, structured outputs, LangGraph pipeline, schema generation, visual grounding, anti-hallucination, or any Prism-specific code. Covers the multi-agent pipeline (ingest, parse, extract, ground, validate), OpenAI Responses API patterns, Structured Outputs with strict mode, and the abstain-over-guess philosophy."
---

# Prism ADE — Agentic Document Extraction

## Purpose

Project-specific skill for the Prism codebase. Provides architecture context, coding patterns, and guidelines for working on the multi-agent document extraction pipeline.

## When to Use

- Adding or modifying agents in `prism/agents/`
- Working with the LangGraph orchestrator
- Implementing OpenAI Responses API calls
- Modifying extraction schemas or Structured Outputs
- Working on OCR, grounding, or validation logic
- Debugging the extraction pipeline
- Adding API endpoints or Playground features

## Architecture Overview

```
START → ingest → parse → extract → ground → validate → (retry?) → END
                                                  ↓ (fields_to_retry)
                                                extract (re-loop, max 3)
```

### Agents

| Agent | File | Input | Output |
|-------|------|-------|--------|
| IngestNode | `orchestrator.py` | file_path | images, OCR, digital_text |
| ParseAgent | `parse_agent.py` | images/text | parsed_markdown (per-page) |
| ExtractAgent | `extract_agent.py` | images/text + schema | extracted_data + _sources |
| GroundingAgent | `grounding_agent.py` | extracted + OCR words | grounding_map (bboxes) |
| ValidatorAgent | `validator_agent.py` | extracted + grounding | final_output + confidence |
| SchemaAgent | `schema_agent.py` | images/text | suggested_schema |

### Core Modules

| Module | File | Role |
|--------|------|------|
| Config | `core/config.py` | Env-based settings via dataclass |
| Types | `core/types.py` | Pydantic models (BBox, OCRWord, Confidence) |
| State | `core/state.py` | DocumentState TypedDict for LangGraph |
| Ingestion | `core/ingestion.py` | PDF routing, image conversion, preprocessing |
| OCR | `core/ocr.py` | Tesseract word-level bounding boxes |
| Grounding | `core/grounding.py` | Fuzzy matching via thefuzz |

## Key Patterns

### 1. OpenAI Responses API (Required)

All agents MUST use the Responses API — NOT Chat Completions.

```python
from openai import OpenAI

client = OpenAI(api_key=settings.openai_api_key)

# Text-only call
resp = client.responses.create(
    model=settings.openai_model,
    instructions=SYSTEM_PROMPT,          # system prompt
    input=[{"role": "user", "content": prompt}],  # user message
    max_output_tokens=4096,
)
result = resp.output_text  # response text

# Vision call (with images)
resp = client.responses.create(
    model=settings.openai_model,
    instructions=SYSTEM_PROMPT,
    input=[{"role": "user", "content": [
        {"type": "input_image", "image_url": f"data:image/png;base64,{b64}", "detail": "high"},
        {"type": "input_text", "text": prompt},
    ]}],
    max_output_tokens=4096,
)
```

**Critical differences from Chat Completions:**
- `instructions=` replaces `messages=[{"role": "system", ...}]`
- `input=` replaces `messages=[{"role": "user", ...}]`
- Content types: `input_image` (not `image_url`), `input_text` (not `text`)
- Response: `resp.output_text` (not `resp.choices[0].message.content`)
- `temperature` is NOT supported by all models (e.g., gpt-5-mini)

### 2. Structured Outputs (extract_agent.py)

Use `json_schema` format with `strict: true` — NOT `json_object`.

```python
text_format = {
    "format": {
        "type": "json_schema",
        "name": "extraction",
        "strict": True,
        "schema": strict_schema,  # from _prepare_strict_schema()
    }
}

resp = client.responses.create(
    model=settings.openai_model,
    instructions=SYSTEM_PROMPT,
    input=[{"role": "user", "content": user_content}],
    text=text_format,
    max_output_tokens=4096,
)
```

**Strict mode requirements:**
- `additionalProperties: false` on ALL objects
- ALL properties listed in `required`
- Nullable types: `["string", "null"]` (not just `"string"`)
- `_sources` mirror object for provenance tracking

### 3. Text-Only Fallback

When Poppler is unavailable, digital PDFs use text-only paths:
- `ingest_node()`: catches pdf_to_images failure, sets `document_images = []`
- All agents check `if not images:` and fall back to `digital_text` or `ocr_full_text`
- `extract_digital_text()` uses `--- Page N ---` markers per page
- `parse_agent` splits on `re.split(r"--- Page \d+ ---\n?", text)` for per-page processing

### 4. Anti-Hallucination: Abstain Over Guess

The ValidatorAgent implements multi-layer verification:

1. **HIGH** confidence: grounding score >= 90 AND source text found in OCR
2. **MEDIUM** confidence: score >= threshold OR value found in ground truth text
3. **LOW** confidence: score >= 50 — schedules re-extraction
4. **UNVERIFIED**: score < 50 — abstains (returns `null`)

**Ground truth fallback**: `ground_truth_text = ocr_full_text or digital_text`

### 5. LangGraph State Flow

```python
# State is a TypedDict — each agent returns a partial dict to merge
def my_agent(state: DocumentState) -> dict:
    # Read from state
    images = state.get("document_images", [])
    # Return updates (merged into state)
    return {"my_output": result}
```

## API Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/v1/extract` | Full extraction pipeline |
| POST | `/v1/parse` | Parse only (markdown + OCR) |
| POST | `/v1/schema/suggest` | Auto-generate JSON schema |
| GET | `/v1/runs/{run_id}` | Retrieve past run |

## Common Commands

```bash
# Run server
uvicorn prism.api.app:app --reload --port 8000

# Run playground
streamlit run prism/playground/app.py

# Run tests
pytest tests/

# Quick extraction test
python -c "
from prism.agents.orchestrator import create_extraction_app
import json
schema = {'type': 'object', 'properties': {...}, 'required': [...]}
app = create_extraction_app()
result = app.invoke({'file_path': 'samples/your.pdf', 'json_schema': schema})
print(json.dumps(result.get('final_output', {}), indent=2))
"
```

## Constraints

- **Approved libraries**: LangGraph, pytesseract, pypdf2, thefuzz, Pillow, pandas, numpy, scipy, OpenAI (Responses API)
- **Cannot use**: LandingAI ADE, PaddleOCR, EasyOCR, Kraken, PyMuPDF
- **GPT-4o Vision** for reading/understanding; **Tesseract** for spatial bounding boxes only
- **No `temperature=0`** — unsupported by some models

## File Structure

```
prism/
  agents/
    orchestrator.py    # LangGraph graph builder + ingest_node
    parse_agent.py     # GPT-4o Vision → markdown
    extract_agent.py   # Structured Outputs → JSON
    grounding_agent.py # thefuzz → bbox mapping
    validator_agent.py # confidence scoring + retry logic
    schema_agent.py    # auto-generate JSON schema
  core/
    config.py          # Settings dataclass + .env
    types.py           # Pydantic models
    state.py           # DocumentState TypedDict
    ingestion.py       # PDF/image loading + preprocessing
    ocr.py             # Tesseract OCR
    grounding.py       # Fuzzy matching engine
  api/
    app.py             # FastAPI endpoints
  playground/
    app.py             # Streamlit UI
```
