# Project Memory — Databricks Agent Lab

## Project
MLflow pyfunc agent that answers employee questions via natural language.
Deployed to Databricks Model Serving. Pure Python, no LangChain.

## Structure
```
databricks-agent-lab-ai/
├── main.py              # entry point
├── .env                 # secrets (never commit)
├── requirements.txt
├── src/
│   ├── agent.py         # EmployeeAgent (MLflow pyfunc PythonModel)
│   ├── tools.py         # SQL tools via Databricks SQL Execution API
│   └── deploy.py        # registers model to UC + creates/updates endpoint
├── FLOW_LOCAL.md        # local run flow diagram
└── FLOW_REMOTE.md       # deployed endpoint flow diagram
```

## How to run
```bash
python main.py                              # deploy to Databricks
python main.py --local "how many employees?"  # test locally
```

## Deployed resources
| | |
|---|---|
| Endpoint | `employee-agent-endpoint` |
| Model (UC) | `workspace.default.employee_agent` |
| Databricks host | `https://dbc-28397b78-e659.cloud.databricks.com` |
| LLM | `system.ai.gemma-3-12b` via AI Gateway |
| Table | `workspace.default.employees` |
| SQL Warehouse | `0d6caddefaa6c3ea` |
| MLflow experiment | `/Users/anuja.poc@gmail.com/employee-agent` |
| UC catalog | `workspace` (not `main`) |

## Request format
```json
{"inputs": [{"question": "how many employees?"}]}
```

## Key decisions
- `openai.OpenAI` client for LLM calls — Databricks SDK `query()` doesn't support `tools`
- `WorkspaceClient` used only for SQL execution
- `code_paths=[tools.py, agent.py]` bundles both files into the MLflow artifact
- `ModelSignature` with named `ColSpec(type="string", name="question")` required for UC

## Known issues / TODO
- SQL cold-start: `_run_sql` does only one retry poll — needs a proper retry loop
- MLflow warnings: `artifact_path` deprecated; CloudPickle warning (use file path approach)

## Notes
- Always use `anuja.poc@gmail.com` for Databricks workspace paths — not Accenture email
