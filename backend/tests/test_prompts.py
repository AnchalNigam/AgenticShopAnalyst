"""Tests for system prompts, schema context, and canonical few-shot SQL queries."""

from __future__ import annotations

import re
from app.agent.prompts import (
    BUSINESS_RULES_PROMPT,
    DB_SCHEMA_PROMPT,
    FEW_SHOT_EXAMPLES,
    SYSTEM_PROMPT,
)
from app.tools.sql_tool import execute_sql_query


class TestPromptStructure:
    """Verify that system prompt contains all critical domain context."""

    def test_schema_prompt_contains_all_tables(self) -> None:
        required_tables = ["customers", "products", "orders", "order_items", "refunds"]
        for table in required_tables:
            assert f"`{table}`" in DB_SCHEMA_PROMPT

    def test_business_rules_prompt_contains_key_metrics(self) -> None:
        assert "completed" in BUSINESS_RULES_PROMPT
        assert "unit_price" in BUSINESS_RULES_PROMPT
        assert "2026" in BUSINESS_RULES_PROMPT
        assert "INR" in BUSINESS_RULES_PROMPT or "₹" in BUSINESS_RULES_PROMPT

    def test_system_prompt_compiles_all_sections(self) -> None:
        assert DB_SCHEMA_PROMPT in SYSTEM_PROMPT
        assert BUSINESS_RULES_PROMPT in SYSTEM_PROMPT
        assert FEW_SHOT_EXAMPLES in SYSTEM_PROMPT


class TestFewShotQueriesAgainstDatabase:
    """Ensure every SQL query documented in few-shot examples actually executes cleanly on Postgres."""

    def test_canonical_queries_execute_successfully(self) -> None:
        # Extract all SQL blocks from FEW_SHOT_EXAMPLES
        sql_blocks = re.findall(r"```sql\s*([\s\S]*?)\s*```", FEW_SHOT_EXAMPLES)
        assert len(sql_blocks) >= 4, "Expected at least 4 few-shot SQL examples."

        for sql in sql_blocks:
            result = execute_sql_query(sql.strip())
            assert result["success"] is True, f"Canonical query failed: {sql}\nError: {result.get('error')}"
            assert len(result["rows"]) > 0, f"Canonical query returned 0 rows: {sql}"
