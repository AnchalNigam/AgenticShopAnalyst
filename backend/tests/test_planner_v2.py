"""Unit and integration tests for V2 Task Planner."""

from __future__ import annotations

import json
import pytest

from app.agent.llm_client import BaseLLMClient, LLMResponse
from app.agent.planner import generate_execution_plan, ExecutionPlan, PlanTask


class MockPlannerLLMClient(BaseLLMClient):
    """Simulates an LLM returning a valid multi-step execution plan."""

    def chat(self, messages: list[dict], system_prompt: str, tools: list[dict] | None = None) -> LLMResponse:
        plan_dict = {
            "reasoning": "Compound question requiring revenue comparison, category breakdown, and cohort refund benchmarking.",
            "tasks": [
                {
                    "id": 1,
                    "title": "Calculate July vs August Revenue",
                    "objective": "Query completed orders revenue for July and August 2026",
                    "sql_needed": True,
                    "expected_output_key": "revenue_growth",
                },
                {
                    "id": 2,
                    "title": "Find Top Category in August",
                    "objective": "Query August revenue by category to identify the top dollar contributor",
                    "sql_needed": True,
                    "expected_output_key": "top_category",
                },
                {
                    "id": 3,
                    "title": "Calculate Refund Benchmarks",
                    "objective": "Calculate August cohort refund rate for company and top category",
                    "sql_needed": True,
                    "expected_output_key": "refund_analysis",
                },
            ],
        }
        return LLMResponse(content=json.dumps(plan_dict), tool_calls=[])


class MockInvalidJSONClient(BaseLLMClient):
    """Simulates an LLM returning malformed non-JSON text."""

    def chat(self, messages: list[dict], system_prompt: str, tools: list[dict] | None = None) -> LLMResponse:
        return LLMResponse(content="Sorry I cannot output JSON right now.", tool_calls=[])


def test_planner_multi_step_decomposition() -> None:
    """Verify that planner correctly parses multi-step plan from LLM."""
    client = MockPlannerLLMClient()
    plan = generate_execution_plan("Compare July vs August revenue and check refunds", client=client)

    assert isinstance(plan, ExecutionPlan)
    assert len(plan.tasks) == 3
    assert plan.tasks[0].id == 1
    assert plan.tasks[0].expected_output_key == "revenue_growth"
    assert plan.tasks[1].expected_output_key == "top_category"
    assert plan.tasks[2].expected_output_key == "refund_analysis"


def test_planner_fallback_on_invalid_json() -> None:
    """Verify that planner gracefully degrades to a single-step fallback plan on malformed output."""
    client = MockInvalidJSONClient()
    plan = generate_execution_plan("What was revenue in August?", client=client)

    assert isinstance(plan, ExecutionPlan)
    assert len(plan.tasks) == 1
    assert plan.tasks[0].id == 1
    assert "Fallback" in plan.reasoning
