"""Deterministic date difference and deadline calculations."""

import re
from datetime import date, timedelta


class DateDeadlineTool:
    name = "Date/Deadline Tool"

    _date_pattern = r"\b(\d{4}-\d{2}-\d{2})\b"
    _duration_pattern = re.compile(
        r"(?:within|after|in)\s+(\d+)\s+(day|days|week|weeks|month|months)\s+(?:of|from|after)?\s*(\d{4}-\d{2}-\d{2})",
        re.IGNORECASE,
    )

    def run(self, text: str) -> dict:
        """Calculate an explicit deadline or the difference between two ISO dates."""
        try:
            duration_match = self._duration_pattern.search(text)
            if duration_match:
                amount = int(duration_match.group(1))
                unit = duration_match.group(2).lower()
                start = date.fromisoformat(duration_match.group(3))
                days = amount * 7 if unit.startswith("week") else amount * 30 if unit.startswith("month") else amount
                deadline = start + timedelta(days=days)
                result = f"{start.isoformat()} + {amount} {unit} = {deadline.isoformat()}"
                return self._success(text, result, "deadline", start.isoformat(), deadline.isoformat())

            dates = [date.fromisoformat(value) for value in re.findall(self._date_pattern, text)]
            if len(dates) >= 2:
                difference = (dates[1] - dates[0]).days
                return self._success(text, f"{dates[0].isoformat()} to {dates[1].isoformat()} = {difference} days", "date_difference", dates[0].isoformat(), dates[1].isoformat())
            raise ValueError("Provide two ISO dates or a duration such as 'within 30 days of 2026-09-06'.")
        except ValueError as exc:
            return {
                "tool": self.name,
                "success": False,
                "input": text,
                "result": None,
                "error": f"Could not calculate date or deadline: {str(exc)[:200]}",
            }

    def _success(self, text: str, result: str, operation: str, start: str, end: str) -> dict:
        return {
            "tool": self.name,
            "success": True,
            "input": text,
            "operation": operation,
            "start": start,
            "end": end,
            "result": result,
        }
