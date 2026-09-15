"""
Employee Agent — packaged as an MLflow pyfunc model so it can be
logged locally, registered to Unity Catalog, and served by Databricks
Model Serving without changing any code.

Local run:   python main.py --local "who is the highest paid?"
Deploy:      python main.py
"""

import json
import os
import sys
from pathlib import Path

import mlflow
import mlflow.pyfunc
import pandas as pd
from databricks.sdk import WorkspaceClient
from openai import OpenAI

sys.path.insert(0, str(Path(__file__).parent))
from tools import TOOL_DEFINITIONS, dispatch_tool
from prompts import SYSTEM_PROMPT


class EmployeeAgent(mlflow.pyfunc.PythonModel):
    """
    MLflow pyfunc wrapper around the employee Q&A agent.

    Input schema (pandas DataFrame):
        messages: list of OpenAI-style chat message dicts
                  e.g. [{"role": "user", "content": "Who is the highest paid?"}]

    Output: string — the agent's final answer
    """

    def load_context(self, context):
        # OpenAI client for LLM calls (supports tools/tool_choice)
        self.llm = OpenAI(
            api_key=os.environ["DATABRICKS_TOKEN"],
            base_url=f"{os.environ['DATABRICKS_HOST']}/ai-gateway/mlflow/v1",
        )
        # WorkspaceClient for SQL execution in tools
        self.workspace_client = WorkspaceClient()
        self.model_endpoint = os.environ.get("AI_MODEL_ENDPOINT", "system.ai.gemma-3-12b")

    def predict(self, context, model_input: pd.DataFrame, params=None) -> list[str]:
        return [
            self._run_agent([{"role": "user", "content": q}])
            for q in model_input["question"]
        ]

    def _run_agent(self, messages: list[dict]) -> str:
        """Agentic loop: call model → execute tools → repeat until done."""
        conversation = [{"role": "system", "content": SYSTEM_PROMPT}] + list(messages)

        for _ in range(10):
            response = self.llm.chat.completions.create(
                model=self.model_endpoint,
                messages=conversation,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                max_tokens=1024,
            )

            assistant_msg = response.choices[0].message

            # Serialize back to dict so conversation stays JSON-serializable
            msg_dict = {"role": "assistant", "content": assistant_msg.content}
            if assistant_msg.tool_calls:
                msg_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in assistant_msg.tool_calls
                ]
            conversation.append(msg_dict)

            if not assistant_msg.tool_calls:
                return assistant_msg.content or ""

            for tool_call in assistant_msg.tool_calls:
                fn = tool_call.function
                tool_result = dispatch_tool(
                    self.workspace_client,
                    fn.name,
                    json.loads(fn.arguments),
                )
                conversation.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                })

        return "Agent reached max iterations without a final answer."


# ── Local test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    agent = EmployeeAgent()

    class _FakeContext:
        model_config = {}

    agent.load_context(_FakeContext())

    question = sys.argv[1] if len(sys.argv) > 1 else "how many employees?"
    print(f"\nQuestion: {question}")

    df = pd.DataFrame({"question": [question]})
    answers = agent.predict(None, df)
    print(f"Answer: {answers[0]}")
