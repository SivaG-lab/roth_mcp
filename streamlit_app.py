"""Streamlit Chat UI for Roth Conversion Calculator."""

from __future__ import annotations

import asyncio
import json
import logging

import nest_asyncio
import streamlit as st
import streamlit.components.v1 as components

from config import OPENAI_API_KEY, OPENAI_MODEL, MAX_SESSION_COST, validate_config
from models import (
    UserProfile,
    ModelAssumptions,
    CalculationResults,
    TokenTracker,
    PipelinePhase,
)
from mcp_client import MCPConnection, discover_tools, ResilientToolExecutor
from agent_loop import agent_loop

logger = logging.getLogger(__name__)
from dual_return import extract_html

_APP_STATE_KEYS = {
    "messages", "profile", "assumptions", "results",
    "html_cards", "token_data", "pipeline_phase",
    "mcp_session", "openai_tools", "executor",
}


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------

def initialize_session_state():
    """Initialize all session state keys if not already set."""
    defaults = {
        "messages": [],
        "profile": UserProfile(),
        "assumptions": ModelAssumptions(),
        "results": CalculationResults(),
        "html_cards": {},
        "token_data": TokenTracker(),
        "pipeline_phase": PipelinePhase.COLLECTING,
        "mcp_session": None,
        "openai_tools": [],
        "executor": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ---------------------------------------------------------------------------
# MCP session (cached)
# ---------------------------------------------------------------------------

@st.cache_resource
def get_mcp_resources():
    """Initialize MCP session and tool definitions (cached across reruns)."""
    loop = asyncio.new_event_loop()
    try:
        conn = MCPConnection()
        session = loop.run_until_complete(conn.connect())
        tools = loop.run_until_complete(discover_tools(session))

        async def session_factory():
            """Reconnect factory for ResilientToolExecutor."""
            await conn.close()
            return await conn.connect()

        executor = ResilientToolExecutor(session, session_factory=session_factory)
        return session, tools, executor, loop, conn
    except Exception:
        return None, [], None, loop, None


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

def render_sidebar():
    """Render sidebar with profile, assumptions, results, and usage."""
    with st.sidebar:
        st.title("Roth Conversion Calculator")
        st.caption("MCP v2.0")

        # User profile
        st.subheader("User Profile")
        profile = st.session_state.profile
        if profile.current_age:
            st.write(f"**Age:** {profile.current_age}")
        if profile.filing_status:
            st.write(f"**Filing:** {profile.filing_status}")
        if profile.state:
            st.write(f"**State:** {profile.state}")
        if profile.annual_income:
            st.write(f"**Income:** ${profile.annual_income:,.0f}")
        if profile.trad_ira_balance:
            st.write(f"**IRA Balance:** ${profile.trad_ira_balance:,.0f}")

        # Model assumptions
        st.subheader("Assumptions")
        assumptions = st.session_state.assumptions
        st.write(f"Return: {assumptions.annual_return:.0%}")
        st.write(f"Model Years: {assumptions.model_years}")
        st.write(f"Inflation: {assumptions.inflation_rate:.0%}")

        # Calculation results summary
        results = st.session_state.results
        if results.tools_completed:
            st.subheader("Results")
            if results.tax_estimate:
                st.write(f"**Tax Cost:** ${results.tax_estimate.total_tax_cost:,.0f}")
            if results.breakeven:
                st.write(f"**Breakeven:** {results.breakeven.breakeven_years} years")
                st.write(f"**Assessment:** {results.breakeven.assessment}")

        # API Usage
        st.subheader("API Usage")
        tracker = st.session_state.token_data
        st.write(f"Tokens: {tracker.total_prompt_tokens + tracker.total_completion_tokens:,}")
        st.write(f"Est. Cost: ${tracker.estimated_cost:.4f}")
        st.write(f"Model: {OPENAI_MODEL}")

        # Start Over
        if st.button("Start Over", type="secondary"):
            for key in list(st.session_state.keys()):
                if key in _APP_STATE_KEYS:
                    del st.session_state[key]
            get_mcp_resources.clear()
            st.rerun()


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------

def main():
    nest_asyncio.apply()
    st.set_page_config(
        page_title="Roth Conversion Calculator",
        page_icon="💰",
        layout="wide",
    )

    initialize_session_state()
    render_sidebar()

    # Welcome message
    if not st.session_state.messages:
        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                "Welcome! I'm your Roth IRA conversion analysis assistant. "
                "I can help you analyze the tax impact of converting traditional IRA funds to a Roth IRA.\n\n"
                "To get started, tell me about your situation — your age, filing status, "
                "state, income, IRA balance, and how much you're thinking of converting."
            ),
        })

    # Display chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Display HTML cards
    for tool_name, html_str in st.session_state.html_cards.items():
        if html_str and "<div" in html_str:
            if tool_name == "generate_conversion_report":
                components.html(html_str, height=800, scrolling=True)
            else:
                st.html(html_str)

    # Chat input
    if user_input := st.chat_input("Type your message..."):
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_input)
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Check API key
        if not OPENAI_API_KEY:
            st.error("OPENAI_API_KEY not set. Copy .env.example to .env and add your key.")
            return

        # Get MCP resources
        session, tools, executor, loop, _conn = get_mcp_resources()
        if session is None:
            st.error("Failed to connect to MCP server. Check that mcp_server.py is available.")
            return

        # Run agent loop
        with st.status("Analyzing...", expanded=True) as status:
            try:
                assistant_text, html_outputs = loop.run_until_complete(
                    agent_loop(
                        user_message=user_input,
                        messages=st.session_state.messages,
                        executor=executor,
                        openai_tools=tools,
                        token_tracker=st.session_state.token_data,
                    )
                )

                # Update HTML cards
                st.session_state.html_cards.update(html_outputs)

                # Display assistant response
                with st.chat_message("assistant"):
                    st.markdown(assistant_text)

                # Render new HTML cards
                for tool_name, html_str in html_outputs.items():
                    if html_str and "<div" in html_str:
                        if tool_name == "generate_conversion_report":
                            components.html(html_str, height=800, scrolling=True)
                            # Download button
                            st.download_button(
                                "Download Report",
                                html_str,
                                file_name="roth_conversion_report.html",
                                mime="text/html",
                            )
                        else:
                            st.html(html_str)

                status.update(label="Complete", state="complete")
            except Exception as e:
                status.update(label="Error", state="error")
                logger.error("Agent loop error: %s", e, exc_info=True)
                st.error("An error occurred during analysis. Please try again.")


if __name__ == "__main__":
    main()
