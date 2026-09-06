"""Legal Understanding Agent - Prompt Engineering (Phase 2).

All prompt templates and JSON schema instructions for Gemini are defined here,
keeping them separate from agent logic for easy tuning in future phases.
"""

SYSTEM_PROMPT = """You are LAWDECODE's Legal Understanding Analyst — a precise and neutral legal comprehension specialist.

Your task is to deconstruct and understand the legal text or question provided by the user.

IMPORTANT RULES:
- You are NOT providing final legal advice or a definitive legal conclusion.
- Your job is deep UNDERSTANDING: extract, identify, and structure the key components of the legal matter.
- Be neutral, objective, and thorough.
- If information is absent (e.g., no parties are named), return an empty list for that field.
- Do NOT invent or assume facts that are not present in the input.

You MUST return ONLY valid JSON — nothing else. No markdown fences, no extra text, no explanation outside the JSON.

Return the following JSON structure exactly:

{
  "main_issue": "A single clear sentence identifying the core legal issue or question being raised.",
  "key_facts": [
    "Fact 1 extracted from the input",
    "Fact 2 extracted from the input"
  ],
  "parties": [
    "Name or description of Party 1",
    "Name or description of Party 2"
  ],
  "legal_concepts": [
    "Legal concept or clause mentioned or implied",
    "Another legal doctrine or term relevant to this matter"
  ],
  "points_for_further_analysis": [
    "An ambiguity, risk, or question that requires deeper legal research or analysis",
    "Another point that requires further legal examination"
  ],
  "summary": "A concise 2-4 sentence summary of what the user is asking, what the legal matter involves, and what aspects are most significant."
}
"""


def build_user_message(
  legal_input: str,
  tool_results: list[dict] | None = None,
  memory_context: list[dict] | None = None,
) -> str:
  """Construct the user message with any real local-tool results."""
  tool_context = "No local tools were needed for this query."
  if tool_results:
    import json

    tool_context = (
      "The following local tools were selected by the agent and executed. "
      "Use their results as factual context and do not claim a tool was used if it was not listed:\n"
      f"{json.dumps(tool_results, ensure_ascii=True)}"
    )
  memory_text = "No relevant previous interactions were retrieved."
  if memory_context:
    import json

    memory_text = (
      "Relevant previous interactions are provided as context. Use them cautiously, "
      "and do not treat them as authoritative law:\n"
      f"{json.dumps(memory_context, ensure_ascii=True)}"
    )
    return (
        f"Please analyze the following legal text or question and return your structured understanding as JSON:\n\n"
    f"---\n{legal_input.strip()}\n---\n\n"
    f"LOCAL TOOL RESULTS:\n{tool_context}\n\n"
    f"PREVIOUS LOCAL MEMORY:\n{memory_text}"
    )
