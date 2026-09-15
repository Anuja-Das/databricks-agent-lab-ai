"""
Deploy the EmployeeAgent to Databricks Model Serving.

Steps this script runs:
  1. Authenticate to Databricks (reads .env)
  2. Log the agent as an MLflow model → registers it to Unity Catalog
  3. Create (or update) a Model Serving endpoint
"""

import os
import sys
from pathlib import Path

import mlflow
import mlflow.pyfunc
from mlflow.models import ModelSignature
from mlflow.types.schema import ColSpec, Schema
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.serving import (
    EndpointCoreConfigInput,
    ServedEntityInput,
)

sys.path.insert(0, str(Path(__file__).parent))
from agent import EmployeeAgent

DATABRICKS_HOST   = os.environ["DATABRICKS_HOST"]
UC_CATALOG        = os.environ.get("UC_CATALOG", "workspace")
UC_SCHEMA         = os.environ.get("UC_SCHEMA", "default")
MODEL_NAME        = f"{UC_CATALOG}.{UC_SCHEMA}.employee_agent"
ENDPOINT_NAME     = "employee-agent-endpoint"
EXPERIMENT_NAME   = os.environ.get("MLFLOW_EXPERIMENT_NAME", "/Users/anuja.poc@gmail.com/employee-agent")


def register_model() -> str:
    """Log and register the agent; returns the new model version string."""
    print(f"Registering model to Unity Catalog: {MODEL_NAME}")

    mlflow.set_tracking_uri("databricks")
    mlflow.set_registry_uri("databricks-uc")
    mlflow.set_experiment(EXPERIMENT_NAME)

    conda_env = {
        "channels": ["defaults"],
        "dependencies": [
            "python=3.13",
            {
                "pip": [
                    "databricks-sdk>=0.32.0",
                    "mlflow>=2.16.0",
                    "pandas>=2.0.0",
                    "openai>=1.0.0",
                ]
            },
        ],
    }

    signature = ModelSignature(
        inputs=Schema([ColSpec(type="string", name="question")]),
        outputs=Schema([ColSpec(type="string")]),
    )
    input_example = {"question": "how many employees?"}

    src_dir = Path(__file__).parent
    with mlflow.start_run(run_name="employee-agent-deploy"):
        model_info = mlflow.pyfunc.log_model(
            artifact_path="agent",
            python_model=EmployeeAgent(),
            code_paths=[str(src_dir / "tools.py"), str(src_dir / "agent.py"), str(src_dir / "prompts.py")],
            conda_env=conda_env,
            signature=signature,
            input_example=input_example,
            registered_model_name=MODEL_NAME,
        )

    version = model_info.registered_model_version
    print(f"Registered as version: {version}")
    return version


def deploy_endpoint(model_version: str):
    """Create the serving endpoint (or update it if it already exists)."""
    w = WorkspaceClient()

    served_entity = ServedEntityInput(
        entity_name=MODEL_NAME,
        entity_version=model_version,
        scale_to_zero_enabled=True,
        workload_size="Small",
        environment_vars={
            "DATABRICKS_HOST":         os.environ["DATABRICKS_HOST"],
            "DATABRICKS_TOKEN":        os.environ["DATABRICKS_TOKEN"],
            "DATABRICKS_WAREHOUSE_ID": os.environ["DATABRICKS_WAREHOUSE_ID"],
            "EMPLOYEES_TABLE":         os.environ.get("EMPLOYEES_TABLE", "workspace.default.employees"),
            "AI_MODEL_ENDPOINT":       os.environ.get("AI_MODEL_ENDPOINT", "system.ai.gemma-3-12b"),
            "GENIE_SPACE_ID":          os.environ["GENIE_SPACE_ID"],
            "PYTHONUNBUFFERED":        "1",
        },
    )

    config = EndpointCoreConfigInput(name=ENDPOINT_NAME, served_entities=[served_entity])

    existing = [e.name for e in w.serving_endpoints.list()]
    if ENDPOINT_NAME in existing:
        print(f"Updating existing endpoint: {ENDPOINT_NAME}")
        w.serving_endpoints.update_config_and_wait(name=ENDPOINT_NAME, served_entities=[served_entity])
    else:
        print(f"Creating new endpoint: {ENDPOINT_NAME}")
        w.serving_endpoints.create_and_wait(name=ENDPOINT_NAME, config=config)

    endpoint_url = f"{DATABRICKS_HOST}/serving-endpoints/{ENDPOINT_NAME}/invocations"
    print(f"\nEndpoint ready: {endpoint_url}")
    print("\nTest it with:")
    print(f'  curl -X POST {endpoint_url} \\')
    print(f'    -H "Authorization: Bearer $DATABRICKS_TOKEN" \\')
    print(f'    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"inputs": [{{"question": "how many employees?"}}]}}\'')
