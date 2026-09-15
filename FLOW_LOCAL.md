# Local Flow

**Run:** `python main.py --local "your question"`

---

## What happens

```
main.py --local "who is the highest paid?"
    │
    ├─► OpenAI client
    │       URL  : DATABRICKS_HOST/ai-gateway/mlflow/v1
    │       Model: system.ai.gemma-3-12b
    │       Input: system prompt + user question + tool definitions
    │       └── Gemma decides which tool to call
    │
    ├─► dispatch_tool() → SQL Execution API (WorkspaceClient)
    │       Warehouse: DATABRICKS_WAREHOUSE_ID
    │       Query    : SELECT employee_id, name, salary
    │                  FROM workspace.default.employees
    │                  ORDER BY salary DESC LIMIT 1
    │       Result   : {"employee_id": 3, "name": "Alice", "salary": 95000}
    │
    └─► OpenAI client (second call)
            Input : full conversation + tool result
            Output: "Alice is the highest paid with a salary of $95,000."

Answer printed to terminal
```

---

## Key points

| | |
|---|---|
| **Who orchestrates** | Your local machine |
| **LLM** | Databricks AI Gateway → Gemma 3 12B |
| **Data** | Databricks SQL Warehouse → `workspace.default.employees` |
| **Auth** | PAT from `.env` (`DATABRICKS_TOKEN`) |
| **Data leaves Databricks?** | No — local machine only makes API calls |
