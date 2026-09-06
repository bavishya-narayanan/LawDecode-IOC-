"""Local legal text extraction and organization tool."""

import re


class LegalTextTool:
    name = "Legal Text Tool"
    _patterns = {
        "termination": r"\b(terminate|termination|renewal|notice|cure)\b",
        "financial": r"\b(payment|fee|price|refund|damages|liability|indemnif(?:y|ication))\b",
        "confidentiality": r"\b(confidential|non[- ]?disclosure|trade secret)\b",
        "data_and_ip": r"\b(data|privacy|personal information|intellectual property|license|ownership)\b",
        "dispute": r"\b(governing law|jurisdiction|arbitration|dispute|court|venue)\b",
    }

    def run(self, text: str) -> dict:
        """Extract sentences containing important legal terms and group them."""
        sentences = [part.strip() for part in re.split(r"(?<=[.!?;])\s+|\n+", text) if part.strip()]
        clauses = []
        for sentence in sentences:
            categories = [
                category
                for category, pattern in self._patterns.items()
                if re.search(pattern, sentence, re.IGNORECASE)
            ]
            if categories:
                clauses.append({"categories": categories, "text": sentence})
        return {
            "tool": self.name,
            "success": True,
            "input": text,
            "result": {
                "clause_count": len(clauses),
                "clauses": clauses,
            },
        }
