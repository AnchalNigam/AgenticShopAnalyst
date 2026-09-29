"""Tests for AI Business Analyst agent loop and self-correction."""

from __future__ import annotations

import os
import pytest

from app.agent.analyst import ask_business_analyst
from app.agent.llm_client import BaseLLMClient, LLMResponse, ToolCallRequest


class MockSuccessLLMClient(BaseLLMClient):
    """Simulates an LLM that calls execute_sql_query on turn 1 and synthesizes answer on turn 2."""

    def __init__(self) -> None:
        self.call_count = 0

    def chat(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        self.call_count += 1
        if self.call_count == 1:
            # First turn: Model decides to call SQL tool
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="call_1",
                        name="execute_sql_query",
                        args={
                            "query": (
                                "SELECT SUM(total_amount) AS august_revenue "
                                "FROM orders WHERE status = 'completed' "
                                "AND order_date >= '2026-08-01' AND order_date < '2026-09-01';"
                            )
                        },
                    )
                ],
            )
        # Second turn: Model receives SQL data and provides final business answer
        return LLMResponse(
            content="In August 2026, Shoply achieved completed revenue of ₹14,20,500.00.",
            tool_calls=[],
        )


class MockSelfCorrectionLLMClient(BaseLLMClient):
    """Simulates an LLM that makes a typo on turn 1, receives the error, and self-corrects on turn 2."""

    def __init__(self) -> None:
        self.call_count = 0

    def chat(
        self,
        messages: list[dict],
        system_prompt: str,
        tools: list[dict] | None = None,
    ) -> LLMResponse:
        self.call_count += 1
        if self.call_count == 1:
            # Turn 1: Model hallucinates an invalid column name
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="call_bad_sql",
                        name="execute_sql_query",
                        args={"query": "SELECT revnue FROM orders;"},
                    )
                ],
            )
        elif self.call_count == 2:
            # Turn 2: Inspect message history to verify model received the PostgreSQL error
            tool_msg = messages[-1]
            assert tool_msg["role"] == "tool"
            assert tool_msg["content"]["success"] is False
            assert "PostgreSQL Error" in tool_msg["content"]["error"]

            # Self-correct by issuing valid SQL
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCallRequest(
                        id="call_fixed_sql",
                        name="execute_sql_query",
                        args={
                            "query": (
                                "SELECT SUM(total_amount) AS august_revenue "
                                "FROM orders WHERE status = 'completed' "
                                "AND order_date >= '2026-08-01' AND order_date < '2026-09-01';"
                            )
                        },
                    )
                ],
            )
        # Turn 3: Final synthesis
        return LLMResponse(
            content="After correcting the query, August completed revenue is ₹14,20,500.00.",
            tool_calls=[],
        )


def test_agent_loop_success() -> None:
    """Verify standard question -> tool_call -> DB execute -> answer flow."""
    mock_client = MockSuccessLLMClient()
    result = ask_business_analyst("What was our revenue in August?", client=mock_client)

    assert result.success is True
    assert "₹14,20,500.00" in result.answer
    assert result.sql_query is not None
    assert len(result.query_results) == 1
    # Check that the complete lifecycle is recorded
    assert len(result.execution_steps) == 3
    assert result.execution_steps[0].action == "intent_analysis"
    assert result.execution_steps[1].action == "tool_call"
    assert result.execution_steps[2].action == "synthesis"


def test_agent_loop_self_correction() -> None:
    """Verify that a database error triggers self-correction without crashing."""
    mock_client = MockSelfCorrectionLLMClient()
    result = ask_business_analyst("What was our revenue in August?", client=mock_client)

    assert result.success is True
    assert len(result.execution_steps) == 4
    # Step 1 was intent analysis
    assert result.execution_steps[0].action == "intent_analysis"
    # Step 2 was the error / self_correction attempt
    assert result.execution_steps[1].action == "self_correction_attempt"
    # Step 3 was the successful corrected tool call
    assert result.execution_steps[2].action == "tool_call"
    # Step 4 was synthesis
    assert result.execution_steps[3].action == "synthesis"
    assert len(result.query_results) == 1


def test_agent_simulate_error_injection() -> None:
    """Verify that simulate_error=True forces an error on Turn 1 and triggers self-correction."""
    class DynamicSelfHealingClient(BaseLLMClient):
        def __init__(self) -> None:
            self.turn = 0

        def chat(self, messages: list[dict], system_prompt: str, tools: list[dict] | None = None) -> LLMResponse:
            self.turn += 1
            if self.turn == 1:
                # Turn 1: Model issues a standard valid query
                return LLMResponse(
                    content=None,
                    tool_calls=[
                        ToolCallRequest(
                            id="c1",
                            name="execute_sql_query",
                            args={"query": "SELECT SUM(total_amount) FROM orders WHERE status = 'completed';"},
                        )
                    ],
                )
            elif self.turn == 2:
                # Turn 2: Verify that messages contain the simulated failure
                tool_msg = messages[-1]
                assert tool_msg["role"] == "tool"
                assert tool_msg["content"]["success"] is False
                assert "invalid_order_amount" in str(tool_msg["content"]["error"])
                # Heal and retry with valid SQL
                return LLMResponse(
                    content=None,
                    tool_calls=[
                        ToolCallRequest(
                            id="c2",
                            name="execute_sql_query",
                            args={"query": "SELECT SUM(total_amount) FROM orders WHERE status = 'completed';"},
                        )
                    ],
                )
            return LLMResponse(
                content="Revenue is ₹12,00,000.",
                tool_calls=[],
            )

    client = DynamicSelfHealingClient()
    result = ask_business_analyst("Revenue?", client=client, simulate_error=True)
    assert result.success is True
    assert len(result.execution_steps) == 4
    assert result.execution_steps[1].action == "self_correction_attempt"
    assert "invalid_order_amount" in str(result.execution_steps[1].tool_output)
    assert result.execution_steps[2].action == "tool_call"
    assert result.execution_steps[3].action == "synthesis"


@pytest.mark.skipif(
    not (os.getenv("OPENAI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")),
    reason="No LLM API key configured in environment.",
)
def test_live_analyst_query() -> None:
    """Live end-to-end integration test with configured LLM model (Groq, OpenAI, or Gemini)."""
    result = ask_business_analyst("What was our revenue in August?")
    assert result.success is True
    assert result.sql_query is not None
    assert len(result.query_results) > 0
    assert len(result.answer) > 10
    print(f"\nLive Analyst Answer: {result.answer}")
    print(f"Generated SQL: {result.sql_query}")

