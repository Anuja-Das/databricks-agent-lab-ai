"""
Standalone agent to explore the Databricks UC built-in function: ai_analyze_sentiment()

Analyzes the sentiment of text, returning: positive, negative, or mixed.

Function:  ai_analyze_sentiment(content STRING) -> STRING
Docs:      https://docs.databricks.com/aws/en/sql/language-manual/functions/ai_analyze_sentiment

Usage:
    python src/databricks_functions/ai_analyze_sentiment_agent.py "I love this product!"
    python src/databricks_functions/ai_analyze_sentiment_agent.py "The service was terrible."
    python src/databricks_functions/ai_analyze_sentiment_agent.py "It was okay, nothing special."

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


def ai_analyze_sentiment(client: WorkspaceClient, text: str) -> str:
    warehouse_id = os.environ["DATABRICKS_WAREHOUSE_ID"]

    safe_text = text.replace("'", "''")
    sql = f"SELECT ai_analyze_sentiment('{safe_text}') AS sentiment"

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
        raise RuntimeError(f"ai_analyze_sentiment failed: {detail}")

    rows = response.result.data_array or []
    return rows[0][0] if rows else ""


def main():
    if len(sys.argv) < 2:
        print("Usage: python ai_analyze_sentiment_agent.py <text>")
        print("Example: python ai_analyze_sentiment_agent.py 'I love this product!'")
        sys.exit(1)

    text = sys.argv[1]

    print(f"  Text      : {text}")
    print("  Calling ai_analyze_sentiment...")

    client = WorkspaceClient()
    result = ai_analyze_sentiment(client, text)

    print(f"  Sentiment : {result}")


if __name__ == "__main__":
    main()
    # python src/databricks_functions/ai_analyze_sentiment_agent.py "I love this product!"
