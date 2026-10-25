import re
from typing import Optional
from core.parsers.base import BaseLogParser, LogIncident


class DockerBuildLogParser(BaseLogParser):
    def can_parse(self, raw_logs: str) -> bool:
        indicators = ["docker build", "Dockerfile", "ERROR [internal]", "executor failed running", "returned a non-zero code:"]
        return any(ind in raw_logs for ind in indicators)

    def parse(self, raw_logs: str) -> LogIncident:
        incident = LogIncident(
            framework="docker",
            raw_logs=raw_logs,
            failure_summary="Docker container build failure",
            error_type="DockerBuildError",
            failing_file="Dockerfile",
            exit_code=1,
        )

        # Look for executor failed running [cmd]: exit code: X
        step_match = re.search(r"ERROR\s+\[(\d+/\d+)\]\s+(.+)", raw_logs)
        if step_match:
            incident.failure_summary = f"Docker step {step_match.group(1)} failed: {step_match.group(2).strip()}"

        exit_code_match = re.search(r"returned a non-zero code:\s*(\d+)|exit code:\s*(\d+)", raw_logs)
        if exit_code_match:
            code = exit_code_match.group(1) or exit_code_match.group(2)
            incident.exit_code = int(code)

        # Extract last 20 lines as stack trace
        lines = raw_logs.strip().splitlines()
        incident.stack_trace = "\n".join(lines[-25:])

        return incident
