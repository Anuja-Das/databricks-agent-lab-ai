"""
Standalone agent to explore the Databricks UC built-in function: ai_translate()

NOTE on "NO_SQL": The function's metadata says SQL Data Access = NO_SQL, which means
the function's *implementation* doesn't run SQL queries internally. You still invoke
it via a SQL SELECT statement through a warehouse — that's how all ai_* functions work.

Function:  system.ai.ai_translate(content STRING, language STRING) -> STRING
Docs:      https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_translate

Usage:
    python src/databricks_functions/ai_translate_agent.py "Hello, how are you?" French
    python src/databricks_functions/ai_translate_agent.py "Good morning" Japanese
    python src/databricks_functions/ai_translate_agent.py "I love coding" Spanish

Requires .env with: DATABRICKS_HOST, DATABRICKS_TOKEN, DATABRICKS_WAREHOUSE_ID
"""

import os
import sys
import time
from pathlib import Path

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[2] / ".env")


def ai_translate(client: WorkspaceClient, text: str, target_language: str) -> str:
    warehouse_id = os.environ["DATABRICKS_WAREHOUSE_ID"]

    safe_text = text.replace("'", "''")
    safe_lang = target_language.replace("'", "''")

    sql = f"SELECT ai_translate('{safe_text}', '{safe_lang}') AS translation"

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
        raise RuntimeError(f"ai_translate failed: {detail}")

    rows = response.result.data_array or []
    return rows[0][0] if rows else ""


def main():
    if len(sys.argv) < 3:
        print("Usage: python ai_translate_agent.py <text> <target_language>")
        print("Example: python ai_translate_agent.py 'Hello world' French")
        sys.exit(1)

    text = sys.argv[1]
    target_language = sys.argv[2]

    print(f"  Source text : {text}")
    print(f"  Target lang : {target_language}")
    print("  Calling ai_translate...")

    client = WorkspaceClient()
    result = ai_translate(client, text, target_language)

    print(f"  Translation : {result}")


if __name__ == "__main__":
    main()
    # python src/databricks_functions/ai_translate_agent.py "Hello, how are you?" French
