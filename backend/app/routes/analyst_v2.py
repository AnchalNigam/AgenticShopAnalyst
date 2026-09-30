"""FastAPI route handlers for AgenticShop V2 Plan-and-Solve Business Analyst."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.agent.planner import generate_execution_plan
from app.agent.plan_executor import execute_plan
from app.db import check_db_health
from app.routes.analyst import ExecutionStepModel

router = APIRouter()


class PlanTaskModel(BaseModel):
    id: int
    title: str
    objective: str
    sql_needed: bool
    expected_output_key: str


class ExecutionPlanModel(BaseModel):
    reasoning: str
    tasks: list[PlanTaskModel]


class TaskExecutionResultModel(BaseModel):
    task_id: int
    title: str
    objective: str
    status: str
    sql_query: str | None = None
    query_results: list[dict[str, Any]] = Field(default_factory=list)
    summary: str


class AnalystV2QueryRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=2,
        max_length=500,
        examples=["Compare our revenue growth between July and August, find the top category, and check its refund rate."],
        description="The complex or comparative business question to answer.",
    )


class AnalystV2QueryResponse(BaseModel):
    question: str
    plan: ExecutionPlanModel
    task_results: list[TaskExecutionResultModel]
    scratchpad: dict[str, Any]
    executive_brief: str
    execution_steps: list[ExecutionStepModel]
    success: bool = True
    error: str | None = None


@router.post(
    "/query",
    response_model=AnalystV2QueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Execute compound analytical query using V2 Plan-and-Solve engine",
)
def handle_v2_analyst_query(payload: AnalystV2QueryRequest) -> AnalystV2QueryResponse:
    """Decompose compound question into tasks, execute via scratchpad memory, and deliver verified brief."""
    if not check_db_health():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PostgreSQL database is currently disconnected.",
        )

    try:
        # Step 1: Decompose question into an ExecutionPlan
        plan = generate_execution_plan(payload.question)

        # Step 2: Sequentially execute tasks with scratchpad & reconciler
        exec_result = execute_plan(payload.question, plan)

        return AnalystV2QueryResponse(
            question=exec_result.question,
            plan=ExecutionPlanModel(
                reasoning=exec_result.plan.reasoning,
                tasks=[
                    PlanTaskModel(
                        id=t.id,
                        title=t.title,
                        objective=t.objective,
                        sql_needed=t.sql_needed,
                        expected_output_key=t.expected_output_key,
                    )
                    for t in exec_result.plan.tasks
                ],
            ),
            task_results=[
                TaskExecutionResultModel(
                    task_id=tr.task_id,
                    title=tr.title,
                    objective=tr.objective,
                    status=tr.status,
                    sql_query=tr.sql_query,
                    query_results=tr.query_results,
                    summary=tr.summary,
                )
                for tr in exec_result.task_results
            ],
            scratchpad=exec_result.scratchpad,
            executive_brief=exec_result.executive_brief,
            execution_steps=[
                ExecutionStepModel(
                    step_number=s.step_number,
                    action=s.action,
                    tool_name=s.tool_name,
                    tool_input=s.tool_input,
                    tool_output=s.tool_output,
                    notes=s.notes,
                )
                for s in exec_result.execution_steps
            ],
            success=exec_result.success,
            error=exec_result.error,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"V2 Analysis failed: {exc}",
        )
