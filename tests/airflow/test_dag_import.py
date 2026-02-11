import importlib.util
import os

import pytest


pytest.importorskip("airflow")

DAG_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "pipelines",
        "airflow",
        "dags",
        "tourism_events_pipeline.py",
    )
)


def test_dag_imports():
    spec = importlib.util.spec_from_file_location("tourism_events_pipeline", DAG_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    dag = getattr(module, "dag", None)
    assert dag is not None
    assert dag.dag_id == "tourism_events_pipeline"
