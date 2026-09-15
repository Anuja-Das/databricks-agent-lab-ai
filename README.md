# Databricks Agent Lab

A minimal AI agent that answers natural-language questions about employee data stored in Databricks — built with MLflow, the Databricks SDK, and Gemma 3 12B via the Databricks AI Gateway.

---

## How it works

You ask a question in plain English. The agent sends it to **Gemma 3 12B** (running on Databricks AI Gateway), which decides what SQL to run. It executes that query against **`workspace.default.employees`** using the Databricks SQL Execution API, then passes the result back to Gemma for a final human-readable answer.

```
User question → Gemma (tool decision) → SQL Warehouse → Gemma (final answer) → Response
```

The agent is packaged as an **MLflow pyfunc model**, so the exact same code runs locally on your machine or as a deployed Databricks Model Serving endpoint — no code changes needed between the two modes.

---

## Running it

- **Local** — run the agent on your machine, talking to Databricks APIs: see [FLOW_LOCAL.md](FLOW_LOCAL.md)
- **Deployed** — call the hosted Model Serving endpoint via REST: see [FLOW_REMOTE.md](FLOW_REMOTE.md)
