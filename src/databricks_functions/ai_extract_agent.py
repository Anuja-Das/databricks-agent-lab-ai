"""
Standalone agent to explore the Databricks UC built-in function: ai_extract()

Extracts structured fields from unstructured text using AI.

Function:  ai_extract(content STRING, labels ARRAY<STRING>) -> STRUCT
Docs:      https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_extract

Usage:
    python src/databricks_functions/ai_extract_agent.py \
        "John Smith called from 555-1234 about order #AB123" \
        "name" "phone" "order_id"

    python src/databricks_functions/ai_extract_agent.py \
        "Ship to: 42 Elm Street, Boston, MA 02101" \
        "street" "city" "state" "zip"

Requires .env with: DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID
"""

import json
import os
import sys
import time
from pathlib import Path

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / ".env")


def ai_extract(client: WorkspaceClient, text: str, labels: list[str]) -> dict:
    warehouse_id = os.environ["DATABRICKS_WAREHOUSE_ID"]

    safe_text = text.replace("'", "''")
    labels_sql = ", ".join(f"'{l.replace(chr(39), chr(39)*2)}'" for l in labels)

    sql = f"SELECT to_json(ai_extract('{safe_text}', array({labels_sql}))) AS extracted"

    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="50s",
    )

    terminal = {StatementState.SUCCEEDED, StatementState.FAILED, StatementState.CANCELED, StatementState.CLOSED}
    while response.status.state not in terminal:
        print(f"  Warehouse warming up ({response.status.state})... retrying in 10s")
        time.sleep(10)
        response = client.statement_execution.get_statement(response.statement_id)

    if response.status.state != StatementState.SUCCEEDED:
        err = response.status.error
        detail = f"{err.error_code}: {err.message}" if err else f"state={response.status.state}"
        raise RuntimeError(f"ai_extract failed: {detail}")

    rows = response.result.data_array or []
    raw = rows[0][0] if rows else "{}"
    return json.loads(raw) if raw else {}


def main():
    if len(sys.argv) < 3:
        print("Usage: python ai_extract_agent.py <text> <label1> [label2] ...")
        print("Example: python ai_extract_agent.py 'John called from 555-1234' name phone")
        sys.exit(1)

    text = sys.argv[1]
    labels = sys.argv[2:]

    print(f"  Source text : {text}")
    print(f"  Labels      : {labels}")
    print("  Calling ai_extract...")

    client = WorkspaceClient()
    result = ai_extract(client, text, labels)

    print("  Extracted:")
    for k, v in result.items():
        print(f"    {k}: {v}")


if __name__ == "__main__":
    main()
    # python src/databricks_functions/ai_extract_agent.py "Ship to: 42 Elm Street, Boston, MA 02101" street city state zip
