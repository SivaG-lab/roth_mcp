#!/usr/bin/env python3
"""UserPromptSubmit hook — suggests relevant skills based on user prompt keywords.

Reads skill-rules.json, matches prompt against keyword/intent triggers,
and outputs skill suggestions to stdout (injected into Claude's context).

Usage (stdin): {"session_id": "abc", "prompt": "create a langgraph agent"}
Output (stdout): Formatted skill suggestion text
"""

import json
import re
import sys
from pathlib import Path

SKILLS_DIR = Path(__file__).parent.parent / "skills"
RULES_FILE = SKILLS_DIR / "skill-rules.json"
STATE_DIR = Path(__file__).parent / "state"
MAX_SUGGESTIONS = 3


def load_rules() -> dict:
    """Load skill-rules.json configuration."""
    if not RULES_FILE.exists():
        return {}
    with open(RULES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("skills", {})


def match_skill(prompt_lower: str, rule: dict) -> float:
    """Score how well a prompt matches a skill's triggers. Returns 0.0-1.0."""
    score = 0.0
    triggers = rule.get("promptTriggers", {})

    # Keyword matching
    keywords = triggers.get("keywords", [])
    matched_keywords = sum(1 for kw in keywords if kw.lower() in prompt_lower)
    if keywords:
        score += (matched_keywords / len(keywords)) * 0.6

    # Intent pattern matching
    patterns = triggers.get("intentPatterns", [])
    matched_patterns = 0
    for pattern in patterns:
        try:
            if re.search(pattern, prompt_lower, re.IGNORECASE):
                matched_patterns += 1
        except re.error:
            continue
    if patterns:
        score += (min(matched_patterns, 2) / min(len(patterns), 2)) * 0.4

    return score


def get_session_skills(session_id: str) -> set:
    """Get skills already suggested in this session."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / f"skills-suggested-{session_id}.json"
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            return set()
    return set()


def save_session_skills(session_id: str, skills: set) -> None:
    """Save suggested skills for this session."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state_file = STATE_DIR / f"skills-suggested-{session_id}.json"
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(list(skills), f)


def priority_weight(priority: str) -> float:
    """Weight multiplier for priority levels."""
    return {"critical": 1.5, "high": 1.2, "medium": 1.0, "low": 0.7}.get(priority, 1.0)


def main():
    # Read input from stdin
    try:
        raw = sys.stdin.read().strip()
        if not raw:
            return
        data = json.loads(raw)
    except (json.JSONDecodeError, IOError):
        return

    prompt = data.get("prompt", "")
    session_id = data.get("session_id", "default")

    if not prompt or len(prompt) < 3:
        return

    prompt_lower = prompt.lower()
    rules = load_rules()

    if not rules:
        return

    # Score all skills
    scored = []
    for skill_name, rule in rules.items():
        if rule.get("enforcement") == "block":
            continue  # Block skills handled by PreToolUse hook
        score = match_skill(prompt_lower, rule)
        if score > 0.15:  # Minimum threshold
            weighted = score * priority_weight(rule.get("priority", "medium"))
            scored.append((skill_name, weighted, rule))

    if not scored:
        return

    # Sort by score, take top N
    scored.sort(key=lambda x: x[1], reverse=True)

    # Filter out already-suggested skills in this session
    already_suggested = get_session_skills(session_id)
    candidates = [(name, score, rule) for name, score, rule in scored if name not in already_suggested]

    if not candidates:
        return

    top = candidates[:MAX_SUGGESTIONS]

    # Build suggestion output
    lines = ["<system-reminder>", "Relevant skills detected for this request:"]
    for skill_name, score, rule in top:
        skill_file = SKILLS_DIR / skill_name / "SKILL.md"
        if skill_file.exists():
            lines.append(f"  - **{skill_name}** (.claude/skills/{skill_name}/SKILL.md)")
        else:
            lines.append(f"  - **{skill_name}**")
    lines.append("")
    lines.append("Consider reading these skills for relevant guidance before responding.")
    lines.append("</system-reminder>")

    # Output to stdout (injected into Claude's context)
    print("\n".join(lines))

    # Update session state
    newly_suggested = already_suggested | {name for name, _, _ in top}
    save_session_skills(session_id, newly_suggested)


if __name__ == "__main__":
    main()
