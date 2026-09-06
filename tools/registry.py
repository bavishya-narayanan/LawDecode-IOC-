"""Tool selection and execution for the legal agent pipeline."""

import re
from typing import Any, Dict, List

from .calculator import CalculatorTool
from .date_deadline import DateDeadlineTool
from .legal_text import LegalTextTool


class ToolRegistry:
    """Let Agent 1 decide which deterministic local tools are relevant."""

    def __init__(self):
        self.calculator = CalculatorTool()
        self.date_deadline = DateDeadlineTool()
        self.legal_text = LegalTextTool()

    def run_selected(self, query: str, selected_tools: list[str]) -> List[Dict[str, Any]]:
        """Execute only the named available tools; unknown names are ignored."""
        tools = {
            self.calculator.name: self.calculator,
            self.date_deadline.name: self.date_deadline,
            self.legal_text.name: self.legal_text,
        }
        results = []
        for name in selected_tools:
            tool = tools.get(name)
            if tool is None:
                continue
            if name == self.calculator.name:
                result = tool.run(self._extract_expression(query))
            else:
                result = tool.run(query)
            results.append(result)
        return results

    def run_for_query(self, query: str) -> List[Dict[str, Any]]:
        """Select tools from query signals and execute only selected tools."""
        results = []
        if self._needs_calculator(query):
            expression = self._extract_expression(query)
            results.append(self.calculator.run(expression))
        if self._needs_date_tool(query):
            results.append(self.date_deadline.run(query))
        if self._needs_legal_text_tool(query):
            results.append(self.legal_text.run(query))
        for result in results:
            status = "success" if result.get("success") else "error"
            print(f"[TOOL USED] {result['tool']} ({status})", flush=True)
            print(f"[TOOL RESULT] {result.get('result') or result.get('error')}", flush=True)
        return results

    @staticmethod
    def _needs_calculator(query: str) -> bool:
        return bool(re.search(r"(?:calculate|compute|what is|how much|percent|percentage|\d+\s*[+*/%-]\s*\d+)", query, re.IGNORECASE))

    @staticmethod
    def _extract_expression(query: str) -> str:
        percent_match = re.search(r"(\d+(?:\.\d+)?)\s*%\s*of\s*(\d+(?:\.\d+)?)", query, re.IGNORECASE)
        if percent_match:
            return f"{percent_match.group(1)} / 100 * {percent_match.group(2)}"
        match = re.search(r"(?<![-\d])(\d+(?:\.\d+)?(?:\s*[+*/%-]\s*\d+(?:\.\d+)?)+)(?![-\d])", query)
        if match:
            return match.group(1)
        return "0"

    @staticmethod
    def _needs_date_tool(query: str) -> bool:
        return bool(
            re.search(r"\b(deadline|due date|within \d+|after \d+|before \d+|date difference|days between)\b", query, re.IGNORECASE)
            or len(re.findall(r"\b\d{4}-\d{2}-\d{2}\b", query)) >= 2
        )

    @staticmethod
    def _needs_legal_text_tool(query: str) -> bool:
        return bool(re.search(r"\b(clause|contract|agreement|legal|terminate|termination|liability|indemnity|confidential|notice|governing law)\b", query, re.IGNORECASE))
