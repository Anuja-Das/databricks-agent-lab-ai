# Databricks Agent Lab

A minimal AI agent that answers natural-language questions about employee data stored in Databricks — built with MLflow, the Databricks SDK, and Gemma 3 12B via the Databricks AI Gateway.

---

## Table of Contents

- [How it works](#how-it-works)
- [Running it](#running-it)
- [Databricks AI Functions](#databricks-ai-functions)
  - [ai_translate](#ai_translate)
  - [ai_extract](#ai_extract)
  - [ai_analyze_sentiment](#ai_analyze_sentiment)

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

---

## Databricks AI Functions

Standalone scripts in `src/databricks_functions/` to explore Databricks built-in AI functions. Each script calls the function directly via the SQL Execution API — no LLM agent loop, just the raw function.

All scripts require `.env` with `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, and `DATABRICKS_WAREHOUSE_ID`.

### ai_translate
Translates text into a target language.
```
python src/databricks_functions/ai_translate_agent.py "Hello, how are you?" French
python src/databricks_functions/ai_translate_agent.py "Good morning" Japanese
python src/databricks_functions/ai_translate_agent.py "I love coding" Spanish
```

### ai_extract
Extracts structured fields from unstructured text. Returns a dict of the requested labels.
```
python src/databricks_functions/ai_extract_agent.py "John Smith called from 555-1234 about order #AB123" name phone order_id
python src/databricks_functions/ai_extract_agent.py "Ship to: 42 Elm Street, Boston, MA 02101" street city state zip
python src/databricks_functions/ai_extract_agent.py "Meeting on Friday at 3pm with Alice from Acme Corp" date time person company
```

### ai_analyze_sentiment
Returns the sentiment of text: `positive`, `negative`, or `mixed`.
```
python src/databricks_functions/ai_analyze_sentiment_agent.py "I love this product!"
python src/databricks_functions/ai_analyze_sentiment_agent.py "The service was absolutely terrible."
python src/databricks_functions/ai_analyze_sentiment_agent.py "It was okay, nothing special."
```
