"""SQLite-backed local interaction memory for LAWDECODE."""

from __future__ import annotations

import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.config import BASE_DIR


class LocalMemoryStore:
    """Persist completed analyses and retrieve relevant prior interactions locally."""

    DB_PATH = BASE_DIR / "memory" / "lawdecode.sqlite3"
    _STOP_WORDS = {
        "about", "after", "also", "analyze", "between", "from", "into", "legal",
        "that", "their", "this", "what", "when", "which", "with", "would",
    }

    def __init__(self, db_path: Path | None = None):
        self.db_path = Path(db_path or self.DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(str(self.db_path), timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    query TEXT NOT NULL,
                    agent1_output TEXT NOT NULL,
                    agent2_output TEXT NOT NULL,
                    agent3_output TEXT NOT NULL,
                    final_analysis TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp DESC)"
            )

    def retrieve(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Return recent interactions ranked by simple keyword overlap."""
        try:
            with self._connect() as connection:
                rows = connection.execute(
                    "SELECT * FROM interactions ORDER BY timestamp DESC LIMIT 100"
                ).fetchall()
            query_terms = self._terms(query)
            ranked = []
            for row in rows:
                prior_terms = self._terms(row["query"])
                overlap = len(query_terms & prior_terms)
                if overlap:
                    ranked.append((overlap, row))
            ranked.sort(key=lambda item: (-item[0], item[1]["timestamp"]))
            return [self._row_to_context(row, score) for score, row in ranked[:limit]]
        except (OSError, sqlite3.Error, ValueError, TypeError):
            return []

    def save(
        self,
        query: str,
        agent1_output: dict,
        agent2_output: dict,
        agent3_output: dict,
        final_analysis: dict,
    ) -> bool:
        """Store one completed interaction; return False if local memory is unavailable."""
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO interactions
                    (timestamp, query, agent1_output, agent2_output, agent3_output, final_analysis)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp,
                        query,
                        json.dumps(agent1_output, ensure_ascii=True),
                        json.dumps(agent2_output, ensure_ascii=True),
                        json.dumps(agent3_output, ensure_ascii=True),
                        json.dumps(final_analysis, ensure_ascii=True),
                    ),
                )
            return True
        except (OSError, sqlite3.Error, TypeError, ValueError):
            return False

    @staticmethod
    def _terms(value: str) -> set[str]:
        return {
            term for term in re.findall(r"[a-z0-9]{4,}", value.lower())
            if term not in LocalMemoryStore._STOP_WORDS
        }

    @staticmethod
    def _row_to_context(row: sqlite3.Row, score: int) -> dict[str, Any]:
        def decode(column: str) -> dict:
            try:
                value = json.loads(row[column])
                return value if isinstance(value, dict) else {}
            except (json.JSONDecodeError, TypeError):
                return {}

        return {
            "id": row["id"],
            "timestamp": row["timestamp"],
            "query": row["query"],
            "relevance_score": score,
            "agent1": decode("agent1_output"),
            "agent2": decode("agent2_output"),
            "agent3": decode("agent3_output"),
            "final_analysis": decode("final_analysis"),
        }
