# AgenticShop V2 — Plan-and-Solve Business Analyst Specification

## Overview

**Goal**: Upgrade the AI Business Analyst from a single-shot reactive tool caller (V1) to a **Plan-and-Solve Autonomous Agent (V2)**. When presented with compound, multi-part, or comparative business questions, the agent dynamically decomposes the request into an ordered sequence of atomic sub-tasks, executes each task against PostgreSQL using a shared in-memory scratchpad, reconciles cross-task metrics to prevent data fan-out errors, and delivers an executive brief accompanied by an interactive plan checklist in the UI.

---

## Architecture: The Plan-and-Solve Lifecycle

```text
User Compound Question
         │
         ▼
[1. Dynamic Task Planner (planner.py)]
         │
         ▼ Generates Structured Plan
┌────────────────────────────────────────────────────────┐
│ ExecutionPlan:                                         │
│ • Task 1: Calculate July & August Revenue              │
│ • Task 2: Break Down August Category Revenue           │
│ • Task 3: Calculate August Cohort Category Refunds     │
│ • Task 4: Reconcile Metrics & Synthesize Brief         │
└────────────────────────────────────────────────────────┘
         │
         ▼
[2. Plan Executor & State Machine (plan_executor.py)]
         │
         ├───▶ Task 1 ───▶ execute_sql_query() ───▶ Write to Scratchpad
         ├───▶ Task 2 ───▶ execute_sql_query() ───▶ Write to Scratchpad
         ├───▶ Task 3 ───▶ execute_sql_query() ───▶ Write to Scratchpad
         │
         ▼
[3. Metric Reconciler & Sanity Check]
         │ (Ensures parts sum to whole; validates date baselines)
         ▼
[4. Executive Brief Synthesizer]
         │
         ▼
API Response & Frontend Dashboard
(Interactive Plan Checklist + Multi-Metric Charts + Raw Traces)
```

---

## Core Differences Between V1 and V2

| Capability | Version 1 (Reactive Tool Caller) | Version 2 (Plan-and-Solve Agent) |
| :--- | :--- | :--- |
| **Execution Paradigm** | Single-shot loop with improvised tool calls | Upfront Task Decomposition into atomic sub-tasks |
| **Context Management** | Giant append-only chat history (token bloat) | **Structured Scratchpad**: tasks receive only verified state |
| **Complex Analytical Queries** | Prone to Cartesian fan-out and date mismatches | Each metric evaluated at its correct table grain |
| **Sanity Guardrail** | None (accepts invalid numbers silently) | **Automated Reconciler**: audits mathematical consistency |
| **User Observability** | Single spinner + raw query log | **Live Plan Checklist**: user watches sub-tasks complete |

---

## Core Data Structures

### 1. `PlanTask` & `ExecutionPlan`
```python
class PlanTask(BaseModel):
    id: int
    title: str
    objective: str
    sql_required: bool
    expected_output_key: str

class ExecutionPlan(BaseModel):
    reasoning: str
    tasks: list[PlanTask]
```

### 2. `ExecutionScratchpad`
```python
class ExecutionScratchpad:
    """Thread-safe state accumulator shared across planned sub-tasks."""
    def set(self, key: str, value: Any) -> None: ...
    def get(self, key: str, default: Any = None) -> Any: ...
    def to_dict(self) -> dict[str, Any]: ...
```

---

## Implementation Phases

### Phase 1: Planning Specification & Git Sync [COMPLETED]
- [x] Document architectural differences between V1 and V2.
- [x] Create `specs/v2/v2_planning_analyst_plan.md`.
- [x] Commit and push specification to GitHub.

### Phase 2: Dynamic Task Planner (`backend/app/agent/planner.py`)
- [ ] Define Pydantic models for `PlanTask` and `ExecutionPlan`.
- [ ] Create specialized Planner Prompt that enforces:
  - Table grain awareness (e.g. `orders` vs `order_items` vs `refunds`).
  - Strict date baseline alignment across comparative tasks.
  - Decomposition into 2 to 5 atomic sub-tasks.
- [ ] Unit tests in `backend/tests/test_planner_v2.py`.

### Phase 3: Plan Executor & Context Scratchpad (`backend/app/agent/plan_executor.py`)
- [ ] Implement `ExecutionScratchpad` to pass facts between sub-tasks without chat history bloat.
- [ ] Implement task execution loop:
  - Executes SQL tool calls for tasks requiring database queries.
  - Self-corrects individual sub-task SQL errors without aborting the entire plan.
  - Stores intermediate findings into the scratchpad.
- [ ] Implement `Reconciler` sanity check ensuring parts do not exceed totals.
- [ ] Unit tests in `backend/tests/test_plan_executor_v2.py`.

### Phase 4: API & Backend Integration (`backend/app/routes/analyst.py`)
- [ ] Add mode switch or endpoint `POST /api/v2/analyst/query` supporting plan-and-solve execution.
- [ ] Return structured response containing:
  - `plan`: The initial decomposed task list.
  - `task_results`: Status, SQL, and data for each completed sub-task.
  - `executive_brief`: Final multi-dimensional synthesis.
  - `scratchpad`: Final reconciled metrics dictionary.
- [ ] Integration tests in `backend/tests/test_api_v2.py`.

### Phase 5: React UI Plan Checklist & Observability
- [ ] Create `<PlanChecklist />` component in `frontend/src/components/PlanChecklist.tsx`.
- [ ] Show animated real-time checklist cards:
  - `[✓] Task 1: July vs August Revenue (+32.26%)`
  - `[✓] Task 2: August Category Contribution (Electronics +₹8.46L)`
  - `[✓] Task 3: Category Refund Rate (Pro-rated 1.87%)`
  - `[✓] Task 4: Reconciled Executive Synthesis`
- [ ] Build and bundle into `backend/app/static/`.

### Phase 6: End-to-End Golden Verification
- [ ] Run compound comparative query against live PostgreSQL:
  - *"Compare our month-over-month revenue growth between July and August, find which category contributed most to that change, and tell me if its refund rate is healthy compared to company average."*
- [ ] Verify that:
  - Total refunds reconcile to exactly ₹1,87,623.29.
  - Electronics refund rate is correctly calculated without join duplication.
  - The plan executes cleanly across all sub-tasks.
