# Remote Flow (Deployed)

**Endpoint:** `POST https://dbc-28397b78-e659.cloud.databricks.com/serving-endpoints/employee-agent-endpoint/invocations`

---

## Request payload

```json
{
    "inputs": [{"question": "who is the highest paid?"}]
}
```

---

## What happens

```
Postman / Client
    │
    │  POST /serving-endpoints/employee-agent-endpoint/invocations
    │  Authorization: Bearer <DATABRICKS_TOKEN>
    │
    ▼
Databricks Model Serving
(employee-agent-endpoint — MLflow pyfunc container)
    │
    ├── predict() receives DataFrame with "question" column
    │
    ▼
_run_agent() — agentic loop
    │
    ├─► Call 1 → AI Gateway (Gemma 3 12B)
    │       sends : system prompt + user question + tool definitions
    │       output: tool_call → get_highest_paid_employee
    │
    ├─► dispatch_tool() → SQL Execution API
    │       warehouse: DATABRICKS_WAREHOUSE_ID
    │       query    : SELECT employee_id, name, salary
    │                  FROM workspace.default.employees
    │                  ORDER BY salary DESC LIMIT 1
    │       result   : {"employee_id": 3, "name": "Alice", "salary": 95000}
    │
    └─► Call 2 → AI Gateway (Gemma 3 12B)
            sends : full conversation + tool result
            output: "Alice is the highest paid with a salary of $95,000."
    │
    ▼
Postman / Client
    {"predictions": ["Alice is the highest paid with a salary of $95,000."]}
```

---

## Deployed resources

| Resource | Value |
|---|---|
| **Endpoint** | `employee-agent-endpoint` |
| **Model (UC)** | `workspace.default.employee_agent` |
| **LLM** | `system.ai.gemma-3-12b` via AI Gateway |
| **Data** | `workspace.default.employees` |
| **Workload size** | Small, scale-to-zero enabled |

---

## Test with curl

```bash
curl -X POST https://dbc-28397b78-e659.cloud.databricks.com/serving-endpoints/employee-agent-endpoint/invocations \
  -H "Authorization: Bearer $DATABRICKS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"inputs": [{"question": "how many employees?"}]}'
```
