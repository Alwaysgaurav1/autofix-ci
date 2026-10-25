import pytest
from pathlib import Path
import sys
from core.orchestrator import AutoFixOrchestrator

BASE_BENCHMARKS = Path(__file__).resolve().parent.parent / "benchmarks"


def test_orchestrator_scenario_1():
    scenario_dir = BASE_BENCHMARKS / "scenario_1_python_calc"
    failure_log = (scenario_dir / "failure.log").read_text(encoding="utf-8")

    orchestrator = AutoFixOrchestrator(
        repo_dir=str(scenario_dir),
        test_command=f"{sys.executable} -m pytest -q",
        max_iterations=2,
    )

    session = orchestrator.remediate(failure_log)
    assert session.success is True
    assert session.total_iterations >= 1
    assert session.pr_result is not None
    assert "calculator.py" in session.final_patch.file_path
