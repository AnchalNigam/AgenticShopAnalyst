"""Tests for safe SQL execution tool and security guardrails."""

from __future__ import annotations

import pytest

from app.tools.sql_tool import clean_sql, execute_sql_query, validate_sql


class TestSQLValidation:
    """Test Layer 1 pre-execution query validation."""

    def test_empty_query_rejected(self) -> None:
        with pytest.raises(ValueError, match="Query cannot be empty"):
            validate_sql("   ")

    def test_mutating_statements_rejected(self) -> None:
        forbidden_queries = [
            "DROP TABLE customers;",
            "DELETE FROM orders WHERE order_id = 1;",
            "UPDATE products SET price = 100;",
            "INSERT INTO customers (name) VALUES ('Hacker');",
            "ALTER TABLE orders ADD COLUMN test text;",
            "TRUNCATE TABLE refunds;",
            "GRANT ALL PRIVILEGES ON DATABASE agenticshop TO public;",
        ]
        for query in forbidden_queries:
            with pytest.raises(ValueError):
                validate_sql(query)

    def test_multi_statement_queries_rejected(self) -> None:
        dangerous = "SELECT 1; DROP TABLE customers;"
        with pytest.raises(ValueError, match="Multi-statement"):
            validate_sql(dangerous)

    def test_valid_select_queries_pass(self) -> None:
        # Standard SELECT
        validate_sql("SELECT customer_id, name FROM customers LIMIT 10;")
        # Common Table Expression (WITH)
        validate_sql("WITH monthly_sales AS (SELECT * FROM orders) SELECT * FROM monthly_sales;")
        # With trailing semicolon and comments
        validate_sql("SELECT * FROM products; -- fetch catalogue")


class TestSQLExecution:
    """Test live execution against PostgreSQL."""

    def test_execute_valid_select(self) -> None:
        result = execute_sql_query("SELECT category, COUNT(*) as cnt FROM products GROUP BY category ORDER BY category;")
        assert result["success"] is True
        assert result["columns"] == ["category", "cnt"]
        assert len(result["rows"]) == 4
        assert result["truncated"] is False
        assert result["execution_time_ms"] > 0

    def test_execute_blocked_query_returns_structured_error(self) -> None:
        result = execute_sql_query("DROP TABLE orders;")
        assert result["success"] is False
        assert "Validation Error" in result["error"]
        assert result["query"] == "DROP TABLE orders;"

    def test_execute_invalid_column_returns_postgres_error_for_self_correction(self) -> None:
        result = execute_sql_query("SELECT non_existent_column FROM orders;")
        assert result["success"] is False
        assert "PostgreSQL Error" in result["error"]
        assert "non_existent_column" in result["error"]

    def test_row_truncation_guards_context_window(self) -> None:
        result = execute_sql_query("SELECT * FROM orders;", max_rows=5)
        assert result["success"] is True
        assert result["row_count"] == 5
        assert len(result["rows"]) == 5
        assert result["truncated"] is True
        assert "truncated" in result["message"].lower()

    def test_canonical_v1_revenue_query(self) -> None:
        # Canonical V1 metric: August completed revenue
        query = (
            "SELECT SUM(total_amount) AS august_revenue "
            "FROM orders "
            "WHERE status = 'completed' "
            "AND order_date >= '2026-08-01' "
            "AND order_date < '2026-09-01';"
        )
        result = execute_sql_query(query)
        assert result["success"] is True
        assert len(result["rows"]) == 1
        august_rev = result["rows"][0]["august_revenue"]
        assert isinstance(august_rev, float)
        assert august_rev > 0
