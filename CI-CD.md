# CI/CD Pipeline

## Stack
- **mise** — manages Python 3.11 + uv
- **uv** — dependency management and virtual environment
- **poethepoet (poe)** — task runner (`poe_tasks.toml`)
- **Databricks CLI** — bundle validate / deploy / run (installed via `databricks/setup-cli` GitHub Action)

---

## CI (Continuous Integration)

Triggers on every push to `main` and on pull requests.

| Step | Command | What it does |
|------|---------|--------------|
| Setup | `jdx/mise-action@v2` | Installs Python 3.11 + uv |
| Setup | `databricks/setup-cli@main` | Installs the Databricks CLI |
| Install | `uv sync --all-groups` | Installs all dependencies (main + dev) |
| Lint | `uv run poe lint` | Runs `ruff check .` to catch style/syntax errors |
| Test | `uv run poe test` | Runs `pytest tests/` to validate core behaviour |
| Validate | `uv run poe bundle-validate` | Validates `databricks.yml` bundle config against the workspace |

---

## CD (Continuous Deployment)

Triggers only when CI completes successfully.

| Step | Command | What it does |
|------|---------|--------------|
| Setup | same as CI | mise + Databricks CLI + uv sync |
| Deploy | `uv run poe bundle-deploy-dev` | Uploads bundle files to the Databricks workspace (dev target) |
| Run | `uv run poe bundle-run-dev` | Triggers `databricks_agent_job` on serverless compute and streams run status |

### Viewing job output
1. Go to **Jobs** in the Databricks UI (or **Workflows**, depending on workspace version)
2. Find `[dev anuja_poc] databricks-agent-job`
3. Click the latest run → task `run_python` → **Logs** → **Standard output**

---

## Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `DATABRICKS_HOST` | Workspace URL e.g. `https://dbc-xxxxx.cloud.databricks.com` |
| `DATABRICKS_TOKEN` | Personal access token or service principal token |
