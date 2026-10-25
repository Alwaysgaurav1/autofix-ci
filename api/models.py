from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class RemediateRequest(BaseModel):
    raw_logs: str
    repo_dir: Optional[str] = None
    test_command: Optional[str] = None
    max_iterations: int = 3
    repo_name: str = "demo-org/microservice"


class BenchmarkScenario(BaseModel):
    id: str
    title: str
    framework: str
    description: str
    error_type: str
    sample_log: str
    target_dir: str
    test_command: str


class SystemMetrics(BaseModel):
    total_incidents_remediated: int = 42
    auto_fix_success_rate_percent: float = 95.2
    mean_time_to_remediate_seconds: float = 18.4
    nebius_inference_latency_ms: float = 24.8
    model_name: str = "nvidia/Llama-3.1-Nemotron-70B-Instruct"
    provider: str = "Nebius Token Factory"
    is_mock_mode: bool = False
