# AgenticShop V1 — Business Analyst with SQL Tool Calling Specification

## Overview

**Goal**: Build an AI-driven Business Analyst for the fictional e-commerce company Shoply. Users can ask natural language business questions about the company's data (e.g. revenue, order volume, category performance, refunds), and the agent will dynamically query the PostgreSQL database using SQL tool calling and return accurate, context-aware business insights.

## Architecture

```text
User Question
     │
     ▼
Agent Controller (System Prompt + DDL Schema + Business Rules)
     │
     ▼
LLM Function Calling (Decides to invoke `execute_sql_query`)
     │
     ▼
Safe SQL Execution Tool (Read-only guard, query validator, row limiter, timeout)
     │
     ▼
PostgreSQL Database (`agenticshop`)
     │
     ▼
Tool Result (Columns, rows, or structured error message)
     │
     ▼ (Self-correction if SQL syntax/column error occurs)
LLM Final Synthesis (Clear business answer in natural language with INR figures)
     │
     ▼
API Response / CLI Output (Answer + Generated SQL + Execution Trace)
```

---

## Core Database Schema & Business Metrics

### Tables
- **`customers`**: `customer_id`, `name`, `signup_date`, `region` (`North`, `South`, `East`, `West`), `city`.
- **`products`**: `product_id`, `product_name`, `category` (`Electronics`, `Fashion`, `Home`, `Beauty`), `price`.
- **`orders`**: `order_id`, `customer_id`, `order_date` (July–Sept 2026), `status` (`completed`, `pending`, `cancelled`), `total_amount`.
- **`order_items`**: `order_item_id`, `order_id`, `product_id`, `quantity`, `unit_price`.
- **`refunds`**: `refund_id`, `order_id`, `refund_date`, `amount`, `reason`.

### Canonical Business Definitions
1. **Revenue**: `SUM(orders.total_amount)` for orders where `status = 'completed'`. Refunds are not subtracted unless explicitly asking for net revenue.
2. **Orders Received**: Total count of all orders (`COUNT(*)`), regardless of status.
3. **Completed Orders**: `COUNT(*)` where `status = 'completed'`.
4. **Product / Category Revenue**: `SUM(order_items.quantity * order_items.unit_price)` from `completed` orders.
5. **Timeline**: Historical seed data spans **July 1, 2026 to September 30, 2026**.
6. **Currency**: All monetary amounts are in Indian Rupees (INR, ₹).

---

## Implementation Phases

### Phase 1: Database Service Layer & Connection Pooling [COMPLETED]
- [x] Manage PostgreSQL connection pooling with `psycopg-pool`.
- [x] Implement `app/db.py` with `init_pool`, `close_pool`, `get_db_connection()`, and `check_db_health()`.
- [x] Wire FastAPI `lifespan` in `app/main.py`.
- [x] Health endpoint `GET /health` verifying live database connectivity.
- [x] Automated tests in `tests/test_health.py`.

### Phase 2: Safe SQL Execution Tool & Guardrails [IN PROGRESS]
- [ ] Implement `app/tools/sql_tool.py`:
  - **Layer 1: Pre-Execution Validator**: Rejects mutations (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`, multi-statements). Requires `SELECT` or `WITH`.
  - **Layer 2: PostgreSQL Read-Only Transaction**: Runs inside `BEGIN READ ONLY` so the DB engine rejects any writes.
  - **Layer 3: Statement Timeout**: `SET LOCAL statement_timeout = '5000ms'` to stop runaway queries.
  - **Layer 4: Row Limiter**: Maximum 50 rows returned to protect LLM context windows.
- [ ] Universal JSON Schema tool definition (`execute_sql_query`).
- [ ] Structured JSON output format enabling LLM self-correction upon database errors.
- [ ] Unit tests in `tests/test_sql_tool.py`.

### Phase 3: Schema Metadata & Business Context Prompts
- [ ] Implement `app/agent/prompts.py`:
  - Concise DDL / schema representations.
  - Metric calculation rules (revenue, completed vs received orders, date bounds).
  - Few-shot examples demonstrating canonical SQL queries for standard business questions.

### Phase 4: Provider-Agnostic LLM Client & Explicit Agent Loop
- [ ] Implement `app/agent/llm_client.py`:
  - Configurable support for Gemini (`google-genai`), OpenAI (`openai`), or Ollama/local endpoints.
- [ ] Implement `app/agent/analyst.py`:
  - Explicit Python tool-calling loop (no heavyweight black-box frameworks).
  - Handles single-turn and multi-turn tool execution.
  - Single-attempt self-correction loop when a SQL syntax/column error is returned by the database.

### Phase 5: API Endpoints, Interactive CLI & Automated Evaluation
- [ ] Endpoint `POST /api/v1/analyst/query`:
  - Request: `{"question": str}`
  - Response: `{"question": str, "answer": str, "sql_query": str, "query_results": list[dict], "execution_steps": list[str]}`
- [ ] Interactive CLI `app/cli.py` for manual queries from the terminal.
- [ ] Automated integration tests verifying canonical questions:
  - *"What was our revenue in August?"*
  - *"Which category generated the most revenue last month?"*
  - *"How many orders did we receive in July?"*
  - *"What was our average order value in August?"*
