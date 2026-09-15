"""
Employee table tools — called by the agent.
Uses Databricks SQL Execution API (works locally and when deployed to Model Serving).
"""

import json
import logging
import os
import time
import threading
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from databricks.sdk.service.dashboards import MessageStatus

logger = logging.getLogger()  # root logger — confirmed visible in Databricks service logs


def _run_sql(client: WorkspaceClient, sql: str) -> list[dict]:
    warehouse_id = os.environ["DATABRICKS_WAREHOUSE_ID"]
    response = client.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=sql,
        wait_timeout="50s",
    )

    # If still running after wait_timeout, poll until done
    if response.status.state in (StatementState.PENDING, StatementState.RUNNING):
        response = client.statement_execution.get_statement(response.statement_id)

    if response.status.state != StatementState.SUCCEEDED:
        err = response.status.error
        detail = f"{err.error_code}: {err.message}" if err else f"state={response.status.state}"
        raise RuntimeError(f"SQL failed: {detail}")

    schema = [col.name for col in response.manifest.schema.columns]
    rows = [dict(zip(schema, row)) for row in (response.result.data_array or [])]
    return rows


def get_highest_paid_employee(client: WorkspaceClient) -> str:
    logger.warning("[tool] get_highest_paid_employee called")
    table = os.environ["EMPLOYEES_TABLE"]
    rows = _run_sql(client, f"""
        SELECT employee_id, name, salary
        FROM {table}
        ORDER BY salary DESC
        LIMIT 1
    """)
    return json.dumps(rows[0] if rows else {})


def get_lowest_paid_employee(client: WorkspaceClient) -> str:
    logger.warning("[tool] get_lowest_paid_employee called")
    table = os.environ["EMPLOYEES_TABLE"]
    rows = _run_sql(client, f"""
        SELECT employee_id, name, salary
        FROM {table}
        ORDER BY salary ASC
        LIMIT 1
    """)
    return json.dumps(rows[0] if rows else {})


def query_genie(client: WorkspaceClient, question: str) -> str:
    """Send a natural language question to Databricks AI/BI Genie and return the answer."""
    logger.warning(f"[tool] query_genie called with: {question}")
    space_id = os.environ["GENIE_SPACE_ID"]

    result_box = [None]
    error_box = [None]

    def _call():
        try:
            result_box[0] = client.genie.start_conversation_and_wait(
                space_id=space_id, content=question
            )
        except Exception as e:
            error_box[0] = e

    thread = threading.Thread(target=_call, daemon=True)
    thread.start()
    logger.warning("[genie] waiting for Genie response...")

    elapsed = 0
    while thread.is_alive():
        time.sleep(5)
        elapsed += 5
        logger.warning(f"[genie] still processing... ({elapsed}s elapsed)")

    thread.join()

    if error_box[0]:
        raise error_box[0]

    msg = result_box[0]
    if msg.status != MessageStatus.COMPLETED:
        return f"Genie query did not complete (status={msg.status})."

    logger.warning(f"[genie] completed in ~{elapsed}s")

    parts = []
    for attachment in (msg.attachments or []):
        if attachment.text:
            parts.append(attachment.text.content)
        elif attachment.query:
            try:
                qr = client.genie.get_message_attachment_query_result(
                    space_id=space_id,
                    conversation_id=msg.conversation_id,
                    message_id=msg.id,
                    attachment_id=attachment.id,
                )
                sr = qr.statement_response
                if sr and sr.result:
                    cols = [c.name for c in sr.manifest.schema.columns]
                    rows = [dict(zip(cols, row)) for row in (sr.result.data_array or [])]
                    parts.append(json.dumps(rows))
            except Exception as e:
                parts.append(f"[query result unavailable: {e}]")

    return "\n".join(parts) if parts else "Genie returned no response."


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_highest_paid_employee",
            "description": (
                "Use this tool ONLY when the user asks for the employee "
                "with the highest salary or highest-paid employee. "
                "Do not use this tool for any other employee query."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_lowest_paid_employee",
            "description": (
                "Use this tool ONLY when the user asks for the employee "
                "with the lowest salary or lowest-paid employee. "
                "Do not use this tool for any other employee query."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_genie",
            "description": (
                "Use this tool for complex analytical questions, multi-step reasoning, "
                "trend analysis, comparisons, or any question that goes beyond simple "
                "lookups — for example: salary distributions, department breakdowns, "
                "ranking across groups, or any question where Genie's AI/BI intelligence "
                "would give a richer answer than a direct SQL fetch."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The natural language question to send to Genie.",
                    }
                },
                "required": ["question"],
            },
        },
    },
]


def dispatch_tool(client: WorkspaceClient, tool_name: str, tool_args: dict) -> str:
    if tool_name == "get_highest_paid_employee":
        return get_highest_paid_employee(client)
    elif tool_name == "get_lowest_paid_employee":
        return get_lowest_paid_employee(client)
    elif tool_name == "query_genie":
        return query_genie(client, tool_args["question"])
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
