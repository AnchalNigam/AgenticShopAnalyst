"""FastAPI route handlers for AI Business Analyst queries and metadata."""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.agent.analyst import ask_business_analyst
from app.db import check_db_health, get_table_counts

router = APIRouter()


class ExecutionStepModel(BaseModel):
    step_number: int
    action: str
    tool_name: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: dict[str, Any] | None = None
    notes: str | None = None


class AnalystQueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        max_length=500,
        examples=["What was our revenue in August?"],
        description="The business question to answer.",
    )
    simulate_error: bool = Field(
        default=False,
        description="If True, injects an intentional database error on Turn 1 to test self-correction.",
    )


class AnalystQueryResponse(BaseModel):
    question: str
    answer: str
    sql_query: str | None = None
    query_results: list[dict[str, Any]] = Field(default_factory=list)
    execution_steps: list[ExecutionStepModel] = Field(default_factory=list)
    success: bool = True
    error: str | None = None


class SystemOverviewResponse(BaseModel):
    database_connected: bool
    table_counts: dict[str, int]
    llm_provider: str
    llm_model: str
    sample_questions: list[str]


@router.post(
    "/query",
    response_model=AnalystQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask a business question to the AI Analyst",
)
def handle_analyst_query(payload: AnalystQueryRequest) -> AnalystQueryResponse:
    """Execute the multi-turn agentic loop to query PostgreSQL and synthesize a business answer."""
    if not check_db_health():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL database is currently disconnected.",
        )

    try:
        result = ask_business_analyst(payload.question, simulate_error=payload.simulate_error)
        return AnalystQueryResponse(
            question=result.question,
            answer=result.answer,
            sql_query=result.sql_query,
            query_results=result.query_results,
            execution_steps=[
                ExecutionStepModel(
                    step_number=s.step_number,
                    action=s.action,
                    tool_name=s.tool_name,
                    tool_input=s.tool_input,
                    tool_output=s.tool_output,
                    notes=s.notes,
                )
                for s in result.execution_steps
            ],
            success=result.success,
            error=result.error,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analyst agent error: {str(exc)}",
        ) from exc


@router.get(
    "/overview",
    response_model=SystemOverviewResponse,
    summary="Get system status, table counts, and sample questions",
)
def get_system_overview() -> SystemOverviewResponse:
    """Return database metrics, current LLM settings, and suggested business questions."""
    db_alive = check_db_health()
    counts = get_table_counts() if db_alive else {}
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

    samples = [
        "What was our revenue in August?",
        "Which category generated the most revenue last month?",
        "How many orders did we receive in July?",
        "What was our average order value in August?",
        "Which region had the most completed orders in August?",
        "How much money was refunded in September?",
    ]

    return SystemOverviewResponse(
        database_connected=db_alive,
        table_counts=counts,
        llm_provider=provider,
        llm_model=model,
        sample_questions=samples,
    )
