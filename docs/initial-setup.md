# AgenticShop — initial setup decisions

This stage deliberately establishes only the application's boundaries:

- FastAPI provides a runnable backend shell and a liveness check.
- PostgreSQL runs in a named Docker volume so data survives container restarts.
- `agenticshop` is created by the official PostgreSQL image from `POSTGRES_DB`.
- No business tables or sample data are created yet, so the data model can be introduced and inspected in the next step.

The future agent loop will be implemented explicitly rather than through an agent framework:

```text
user question -> LLM -> SQL tool -> database result -> LLM answer
```

At this stage, the backend does not connect to PostgreSQL. The connection string is merely defined in `.env.example` so that its ownership and configuration are visible before database access is introduced.
