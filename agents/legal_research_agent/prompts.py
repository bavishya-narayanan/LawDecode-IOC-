"""Legal Research Agent — Prompt Engineering (Phase 3).

All prompt templates for Agent 2. Agent 2 receives Agent 1's structured
understanding and uses Gemini to identify relevant legal areas, applicable
provisions, principles, ambiguities, and points for Agent 3 to analyze.
"""

import json

SYSTEM_PROMPT = """You are LAWDECODE's Legal Research Specialist — Agent 2 in a multi-agent legal intelligence pipeline.

You receive structured output from Agent 1 (Legal Understanding Agent), which has already deconstructed the user's legal query.

Your task is to conduct focused legal research based on Agent 1's findings.

IMPORTANT RULES:
- You are NOT providing final legal advice or a definitive legal opinion.
- Your job is RESEARCH: identify relevant legal areas, applicable provisions, principles, and open issues.
- Be precise, neutral, and comprehensive.
- Base your research strictly on the main issue, legal concepts, and points identified by Agent 1.
- If a field has no relevant items, return an empty list — do NOT invent content.
- Do NOT repeat verbatim what Agent 1 said; add research depth and context.

You MUST return ONLY valid JSON — nothing else. No markdown fences, no extra text outside the JSON.

Return the following JSON structure exactly:

{
  "legal_areas": [
    "A broad area of law relevant to this matter (e.g., Contract Law, Employment Law, IP Law)",
    "Another relevant legal domain"
  ],
  "applicable_provisions": [
    "A specific statute, regulation, clause type, or legal provision that may apply",
    "Another applicable provision or standard contract term"
  ],
  "legal_principles": [
    "A general legal doctrine or principle relevant to this matter",
    "Another applicable legal principle or maxim"
  ],
  "important_considerations": [
    "A practical, procedural, jurisdictional, or enforcement consideration",
    "Another important practical consideration"
  ],
  "ambiguities_and_conflicts": [
    "A legal ambiguity, unsettled point, or potential conflict in the law as it applies here",
    "Another ambiguity or area of legal uncertainty"
  ],
  "points_for_agent3": [
    "A specific issue Agent 3 (Legal Analysis) should focus its risk assessment on",
    "Another specific point requiring deeper analytical scrutiny"
  ],
  "research_summary": "A concise 2-4 sentence summary of the legal research findings, key areas of law implicated, and what Agent 3 should concentrate on."
}
"""


def build_user_message(agent1_output: dict) -> str:
    """Build the prompt message for Agent 2 using Agent 1's structured output."""
    main_issue = agent1_output.get("main_issue", "Not provided")
    legal_concepts = agent1_output.get("legal_concepts", [])
    parties = agent1_output.get("parties", [])
    key_facts = agent1_output.get("key_facts", [])
    points = agent1_output.get("points_for_further_analysis", [])
    summary = agent1_output.get("summary", "Not provided")
    memory_context = agent1_output.get("memory_context", [])

    concepts_str = "\n".join(f"  - {c}" for c in legal_concepts) if legal_concepts else "  - None identified"
    parties_str = "\n".join(f"  - {p}" for p in parties) if parties else "  - None identified"
    facts_str = "\n".join(f"  - {f}" for f in key_facts) if key_facts else "  - None identified"
    points_str = "\n".join(f"  - {p}" for p in points) if points else "  - None identified"
    memory_str = json.dumps(memory_context, ensure_ascii=True) if memory_context else "None retrieved"

    return (
        f"Based on Agent 1's structured legal understanding below, conduct focused legal research "
        f"and return your findings as JSON:\n\n"
        f"---\n"
        f"MAIN ISSUE:\n  {main_issue}\n\n"
        f"KEY FACTS:\n{facts_str}\n\n"
        f"PARTIES:\n{parties_str}\n\n"
        f"LEGAL CONCEPTS IDENTIFIED:\n{concepts_str}\n\n"
        f"POINTS REQUIRING FURTHER ANALYSIS:\n{points_str}\n\n"
        f"AGENT 1 SUMMARY:\n  {summary}\n"
        f"\nRELEVANT PREVIOUS LOCAL MEMORY:\n  {memory_str}\n"
        f"---"
    )
