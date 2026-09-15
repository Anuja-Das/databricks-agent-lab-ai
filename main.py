"""
Entry point for the Databricks Employee Agent project.

Usage:
  python main.py            # deploy the agent to Databricks Model Serving
  python main.py --local    # run the agent locally against a question
"""

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    if "--local" in sys.argv:
        import pandas as pd
        from agent import EmployeeAgent

        idx = sys.argv.index("--local")
        question = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "how many employees?"

        agent = EmployeeAgent()

        class _FakeContext:
            model_config = {}

        agent.load_context(_FakeContext())
        answers = agent.predict(None, pd.DataFrame({"question": [question]}))
        print(f"Answer: {answers[0]}")
    else:
        from deploy import register_model, deploy_endpoint
        version = register_model()
        deploy_endpoint(version)


if __name__ == "__main__":
    main()
