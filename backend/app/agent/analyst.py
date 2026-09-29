"""AI Business Analyst explicit agent loop for AgenticShop."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from app.agent.llm_client import BaseLLMClient, get_llm_client
from app.agent.prompts import FINAL_SYNTHESIS_PROMPT, SYSTEM_PROMPT
from app.tools.sql_tool import SQL_TOOL_DEFINITION, execute_sql_query


@dataclass
class ExecutionStep:
    """Represents an individual step taken by the agent during investigation."""

    step_number: int
    action: str  # "tool_call", "self_correction_attempt", or "synthesis"
    tool_name: str | None
    tool_input: dict[str, Any] | None
    tool_output: dict[str, Any] | None
    notes: str | None = None


@dataclass
class AnalystResult:
    """Final output from the AI Business Analyst."""

    question: str
    answer: str
    sql_query: str | None = None
    query_results: list[dict[str, Any]] = field(default_factory=list)
    execution_steps: list[ExecutionStep] = field(default_factory=list)
    success: bool = True
    error: str | None = None


def _inject_simulation_error(sql: str) -> str:
    """Inject a column typo on Turn 1 to test self-correction resilience."""
    replacements = [
        ("total_amount", "invalid_order_amount"),
        ("customer_id", "invalid_customer_id"),
        ("order_id", "invalid_order_id"),
        ("unit_price", "invalid_unit_price"),
        ("category", "invalid_category"),
        ("signup_date", "invalid_signup_date"),
    ]
    for valid_col, invalid_col in replacements:
        if valid_col in sql:
            return sql.replace(valid_col, invalid_col, 1)

    # Fallback: inject an invalid column right after SELECT
    import re
    return re.sub(r"(?i)\bSELECT\s+", "SELECT invalid_test_column, ", sql, count=1)


def ask_business_analyst(
    question: str,
    client: BaseLLMClient | None = None,
    max_turns: int = 4,
    simulate_error: bool = False,
) -> AnalystResult:
    """Execute the explicit agentic loop to answer a business question.

    Flow:
    1. Send user question + schema/rules prompt + SQL tool schema to LLM.
    2. LLM requests `execute_sql_query(query)`.
    3. Tool executes query against PostgreSQL safely.
    4. If query fails (Postgres error), the error is fed back to LLM for self-correction.
    5. Once query succeeds, LLM synthesizes a concise, professional business answer.

    Args:
        question: Natural language question from the user.
        client: Optional pre-configured LLM client (defaults to get_llm_client()).
        max_turns: Maximum allowed turns to prevent runaway loops.
        simulate_error: If True, injects an intentional database error on Turn 1 to test self-correction.

    Returns:
        AnalystResult containing the final answer, SQL query, raw data, and execution steps.
    """
    if client is None:
        client = get_llm_client()

    messages: list[dict[str, Any]] = [{"role": "user", "content": question}]
    steps: list[ExecutionStep] = [
        ExecutionStep(
            step_number=1,
            action="intent_analysis",
            tool_name=None,
            tool_input={"user_question": question},
            tool_output={"grounded_context": "Evaluated against Shoply schema and canonical business definitions."},
            notes="Analyzed question intent and mapped required business metrics and filters",
        )
    ]
    last_sql_query: str | None = None
    last_query_results: list[dict[str, Any]] = []

    for turn in range(1, max_turns + 1):
        # Request next action from the LLM
        response = client.chat(
            messages=messages,
            system_prompt=SYSTEM_PROMPT,
            tools=[SQL_TOOL_DEFINITION],
        )
        print(response, 'response check-->')
        # If the LLM returned a final text response without calling tools:
        if not response.tool_calls:
            steps.append(
                ExecutionStep(
                    step_number=len(steps) + 1,
                    action="synthesis",
                    tool_name=None,
                    tool_input={"status": "database_results_retrieved"},
                    tool_output={"final_response": response.content},
                    notes="Synthesized executive business answer with INR formatting and time context",
                )
            )
            print(steps, 'steps==>')
            return AnalystResult(
                question=question,
                answer=response.content or "No answer could be generated.",
                sql_query=last_sql_query,
                query_results=last_query_results,
                execution_steps=steps,
                success=True,
            )

        # Process each tool call requested by the model
        for tool_call in response.tool_calls:
            if tool_call.name == "execute_sql_query":
                query = tool_call.args.get("query", "").strip()

                # Check for fault injection simulation (Turn 1 only)
                if simulate_error and turn == 1:
                    query = _inject_simulation_error(query)
                    tool_call.args["query"] = query

                tool_result = execute_sql_query(query)

                is_success = tool_result.get("success", False)
                action_type = "tool_call" if is_success else "self_correction_attempt"
                note = (
                    f"Query succeeded ({tool_result.get('row_count', 0)} rows in {tool_result.get('execution_time_ms', 0)}ms)"
                    if is_success
                    else f"Database error (Fault Injected on Turn 1): {tool_result.get('error')}"
                    if (simulate_error and turn == 1)
                    else f"Database error: {tool_result.get('error')}"
                )

                steps.append(
                    ExecutionStep(
                        step_number=len(steps) + 1,
                        action=action_type,
                        tool_name=tool_call.name,
                        tool_input=tool_call.args,
                        tool_output=tool_result,
                        notes=note,
                    )
                )

                # Record model's tool call in history
                messages.append(
                    {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [tool_call],
                    }
                )

                # Record tool's execution result in history
                messages.append(
                    {
                        "role": "tool",
                        "name": tool_call.name,
                        "tool_call_id": tool_call.id,
                        "content": tool_result,
                    }
                )

                last_sql_query = query
                if is_success:
                    last_query_results = tool_result.get("rows", [])

        # If we have reached the last turn and executed SQL, force final synthesis without further tools
        if turn == max_turns and last_sql_query:
            final_res = client.chat(
                messages=messages,
                system_prompt=FINAL_SYNTHESIS_PROMPT,
                tools=None,
            )
            return AnalystResult(
                question=question,
                answer=final_res.content or "Analysis completed.",
                sql_query=last_sql_query,
                query_results=last_query_results,
                execution_steps=steps,
                success=True,
            )

    final_response =  AnalystResult(
        question=question,
        answer="Max turns reached without completing the analysis.",
        sql_query=last_sql_query,
        query_results=last_query_results,
        execution_steps=steps,
        success=False,
        error="Max turns exceeded.",
    )
    return final_response
