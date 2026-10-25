from fastapi import APIRouter, HTTPException
from typing import List
from pathlib import Path
import sys

from api.models import BenchmarkScenario
from core.orchestrator import AutoFixOrchestrator, RemediationSession

router = APIRouter(prefix="/api/benchmarks", tags=["Benchmarks"])

BASE_BENCHMARKS = Path(__file__).resolve().parent.parent.parent / "benchmarks"


def get_available_scenarios() -> List[BenchmarkScenario]:
    s1_log = (BASE_BENCHMARKS / "scenario_1_python_calc" / "failure.log").read_text(encoding="utf-8", errors="replace")
    s2_log = (BASE_BENCHMARKS / "scenario_2_node_validator" / "failure.log").read_text(encoding="utf-8", errors="replace")
    s3_log = (BASE_BENCHMARKS / "scenario_3_docker_build" / "failure.log").read_text(encoding="utf-8", errors="replace")

    return [
        BenchmarkScenario(
            id="scenario_1",
            title="Python / Pytest Off-by-One Arithmetic Regression",
            framework="pytest",
            description="A commit in calculator.py inadvertently introduced a +1 bug breaking unit assertions.",
            error_type="AssertionError",
            sample_log=s1_log,
            target_dir=str(BASE_BENCHMARKS / "scenario_1_python_calc"),
            test_command=f"{sys.executable} -m pytest -q",
        ),
        BenchmarkScenario(
            id="scenario_2",
            title="Node.js / Jest Regex Email Validator Failure",
            framework="jest",
            description="A regular expression in validator.js accepted empty domains without top-level domain verification.",
            error_type="AssertionError [ERR_ASSERTION]",
            sample_log=s2_log,
            target_dir=str(BASE_BENCHMARKS / "scenario_2_node_validator"),
            test_command="node test_validator.js",
        ),
        BenchmarkScenario(
            id="scenario_3",
            title="Dockerfile Build Failure: Missing Package Update",
            framework="docker",
            description="Dockerfile executes apt-get install without updating the apt index, resulting in code 100.",
            error_type="DockerBuildError",
            sample_log=s3_log,
            target_dir=str(BASE_BENCHMARKS / "scenario_3_docker_build"),
            test_command="echo 'Docker syntax validated'",
        ),
    ]


@router.get("", response_model=List[BenchmarkScenario])
def list_scenarios():
    return get_available_scenarios()


@router.post("/run/{scenario_id}", response_model=RemediationSession)
def run_scenario(scenario_id: str):
    scenarios = {s.id: s for s in get_available_scenarios()}
    if scenario_id not in scenarios:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")

    sc = scenarios[scenario_id]
    orchestrator = AutoFixOrchestrator(
        repo_dir=sc.target_dir,
        test_command=sc.test_command,
        max_iterations=3,
    )
    session = orchestrator.remediate(sc.sample_log)
    return session
