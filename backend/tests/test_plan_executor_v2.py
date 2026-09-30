"""Unit tests for V2 Plan Executor, Scratchpad, and Metric Reconciler."""

from __future__ import annotations

import pytest

from app.agent.llm_client import BaseLLMClient, LLMResponse, ToolCallRequest
from app.agent.planner import ExecutionPlan, PlanTask
from app.agent.plan_executor import (
    ExecutionScratchpad,
    _reconcile_metrics,
    execute_plan,
    PlanExecutionResult,
)


def test_scratchpad_state_management() -> None:
    """Verify that ExecutionScratchpad stores, retrieves, and formats state."""
    scratchpad = ExecutionScratchpad()
    scratchpad.set("july_rev", 4309348.20)
    scratchpad.set("aug_rev", 5699572.65)
    scratchpad.set("top_category", "Electronics")

    assert scratchpad.get("july_rev") == 4309348.20
    assert scratchpad.get("top_category") == "Electronics"
    assert scratchpad.get("missing_key", "default") == "default"

    context_str = scratchpad.to_context_string()
    assert "• july_rev: 4309348.2" in context_str
    assert "• top_category: Electronics" in context_str


def test_reconcile_metrics_catches_fan_out_anomaly() -> None:
    """Verify that reconciler flags when category refund exceeds company total."""
    scratchpad = ExecutionScratchpad()
    scratchpad.set("company_refund_amount", 187623.29)
    # Flawed fan-out value from duplicated join:
    scratchpad.set("category_refund_amount", 278877.97)

    warnings = _reconcile_metrics(scratchpad)
    assert len(warnings) == 1
    assert "Reconciliation Warning" in warnings[0]
    assert "exceeded total company refunds" in warnings[0]


class MockPlanExecutorLLMClient(BaseLLMClient):
    """Simulates an LLM handling sequential sub-tasks and final synthesis."""

    def __init__(self) -> None:
        self.step = 0

    def chat(self, messages: list[dict], system_prompt: str, tools: list[dict] | None = None) -> LLMResponse:
        self.step += 1
        # Step 1: SQL call for Task 1
        if self.step == 1:
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
        # Step 2: Summary for Task 1
        elif self.step == 2:
            return LLMResponse(content="Total completed revenue is ₹1,00,08,920.85.", tool_calls=[])
        # Step 3: Final Synthesis
        return LLMResponse(
            content="Executive Brief: Total completed revenue achieved is ₹1,00,08,920.85.",
            tool_calls=[],
        )


def test_execute_plan_sequential_flow() -> None:
    """Verify end-to-end plan execution with 1 sub-task and final synthesis."""
    plan = ExecutionPlan(
        reasoning="Simple revenue retrieval",
        tasks=[
            PlanTask(
                id=1,
                title="Query Total Revenue",
                objective="Get total revenue across all completed orders",
                sql_needed=True,
                expected_output_key="total_revenue",
            )
        ],
    )
    client = MockPlanExecutorLLMClient()
    result = execute_plan("What was our total revenue?", plan, client=client)

    assert isinstance(result, PlanExecutionResult)
    assert result.success is True
    assert len(result.task_results) == 1
    assert result.task_results[0].status == "completed"
    assert "total_revenue" in result.scratchpad
    assert "Executive Brief" in result.executive_brief
    assert len(result.execution_steps) >= 3
