"""GPT conversation loop — handles input collection and pipeline orchestration."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from config import OPENAI_API_KEY, OPENAI_MODEL, OPENAI_TIMEOUT, MAX_SESSION_COST
from dual_return import extract_data, extract_html, compact_result
from schema_converter import mcp_tool_to_openai_function
from pipeline import run_analysis_pipeline

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system.md"


def _load_system_prompt() -> str:
    """Load the GPT system prompt from file."""
    try:
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            "You are a Roth IRA conversion analysis assistant. "
            "Collect user financial inputs and use the available tools to analyze conversions. "
            "NEVER compute financial numbers yourself — always use tools."
        )


def _extract_numeric_values(data: Any) -> set[float]:
    """Recursively extract all numeric values from nested dicts/lists."""
    values = set()
    if isinstance(data, (int, float)):
        values.add(float(data))
    elif isinstance(data, dict):
        for v in data.values():
            values.update(_extract_numeric_values(v))
    elif isinstance(data, list):
        for item in data:
            values.update(_extract_numeric_values(item))
    return values


def check_hallucinated_numbers(
    gpt_response: str, tool_results: dict[str, dict]
) -> list[str]:
    """Check GPT response for dollar amounts, percentages, or breakeven years
    that don't appear in any tool result.

    Uses numeric comparison instead of substring matching for accuracy.
    """
    suspicious = []

    # Extract all numeric values from tool results
    tool_numbers = _extract_numeric_values(tool_results)
    # Also add common derived values (percentages as decimals)
    derived = set()
    for n in tool_numbers:
        if 0 < n < 1:
            derived.add(round(n * 100, 2))  # 0.22 -> 22.0
        if n > 0:
            derived.add(round(n, 2))
    tool_numbers.update(derived)

    # Extract numbers from GPT response
    dollar_pattern = r"\$([\d,]+(?:\.\d{1,2})?)"
    pct_pattern = r"(\d+(?:\.\d+)?)\s*%"
    year_pattern = r"(\d+)\s*years?\s*(?:to break|until)"

    for match in re.finditer(dollar_pattern, gpt_response):
        raw = match.group(1).replace(",", "")
        try:
            val = float(raw)
            if not any(abs(val - t) < 0.01 for t in tool_numbers):
                suspicious.append(f"${match.group(1)}")
        except ValueError:
            pass

    for match in re.finditer(pct_pattern, gpt_response):
        try:
            val = float(match.group(1))
            if not any(abs(val - t) < 0.1 for t in tool_numbers):
                suspicious.append(f"{match.group(1)}%")
        except ValueError:
            pass

    for match in re.finditer(year_pattern, gpt_response):
        try:
            val = float(match.group(1))
            if not any(abs(val - t) < 0.01 for t in tool_numbers):
                suspicious.append(f"{match.group(1)} years")
        except ValueError:
            pass

    return suspicious


async def agent_loop(
    user_message: str,
    messages: list[dict],
    executor: Any,
    openai_tools: list[dict],
    token_tracker: Any = None,
) -> tuple[str, dict[str, str]]:
    """Run one iteration of the GPT agent loop.

    Args:
        user_message: User's chat message
        messages: Conversation history (mutated in place)
        executor: ResilientToolExecutor for MCP tool calls
        openai_tools: OpenAI function definitions
        token_tracker: Optional TokenTracker to record usage

    Returns:
        (assistant_text, html_outputs) tuple
    """
    client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    # Add system prompt if not present
    if not messages or messages[0].get("role") != "system":
        messages.insert(0, {"role": "system", "content": _load_system_prompt()})

    # Ensure user message is in history (caller should have added it)
    if not messages or messages[-1].get("content") != user_message:
        messages.append({"role": "user", "content": user_message})

    # Trim conversation to keep system prompt + last N messages
    max_messages = 40
    if len(messages) > max_messages + 1:  # +1 for system prompt
        messages[:] = [messages[0]] + messages[-(max_messages):]

    html_outputs: dict[str, str] = {}
    tool_data: dict[str, dict] = {}
    pipeline_result = None
    max_iterations = 10

    for iteration in range(max_iterations):
        logger.debug("Agent loop iteration %d", iteration + 1)

        # Enforce session cost limit
        if token_tracker and token_tracker.estimated_cost >= MAX_SESSION_COST:
            return (
                f"Session cost limit (${MAX_SESSION_COST:.2f}) reached. "
                "Please start a new session to continue.",
                html_outputs,
            )

        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=openai_tools if openai_tools else None,
            tool_choice="auto" if openai_tools else None,
            parallel_tool_calls=False,
            timeout=OPENAI_TIMEOUT,
        )

        if token_tracker:
            token_tracker.record(response)

        if not response.choices:
            return "No response from the model. Please try again.", html_outputs

        choice = response.choices[0]
        message = choice.message

        # If no tool calls, return the text response
        if not message.tool_calls:
            assistant_text = message.content or ""
            messages.append({"role": "assistant", "content": assistant_text})

            # Anti-hallucination check
            suspicious = check_hallucinated_numbers(assistant_text, tool_data)
            if suspicious:
                warning = (
                    "\n\n⚠️ *Note: Some numbers in this response could not be verified "
                    "against tool results. Please refer to the analysis cards above for "
                    "accurate figures.*"
                )
                assistant_text += warning

            # Include pipeline HTML if available
            if pipeline_result:
                html_outputs.update({
                    k: extract_html(v)
                    for k, v in pipeline_result.get("html_cards", {}).items()
                    if isinstance(v, str) and v
                })

            return assistant_text, html_outputs

        # Process tool calls
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in message.tool_calls
            ],
        })

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}

            try:
                result = await executor.call_tool(tool_name, arguments)
                result_data = extract_data(result)
                tool_data[tool_name] = result_data

                # Store HTML for display
                html_outputs[tool_name] = extract_html(result)

                # Compact result for GPT context
                compacted = compact_result(tool_name, result)
                tool_response = json.dumps(compacted)

                # Check if pipeline should trigger
                if (tool_name == "validate_projection_inputs"
                        and result_data.get("status") == "complete"
                        and pipeline_result is None):
                    pipeline_result = await run_analysis_pipeline(executor, result_data)
                    # Add pipeline summary to context
                    pipeline_summary = {
                        k: v for k, v in pipeline_result.get("compacted", {}).items()
                    }
                    tool_response = json.dumps({
                        **compacted,
                        "pipeline_completed": True,
                        "pipeline_results": pipeline_summary,
                    })

            except Exception as e:
                logger.error("Tool call %s failed: %s", tool_name, e)
                tool_response = json.dumps({"error": str(e)})

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_response,
            })

    # Max iterations reached
    return "I've reached the maximum number of processing steps. Please try again.", html_outputs
