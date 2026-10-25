import re
from typing import Optional
from core.parsers.base import BaseLogParser, LogIncident


class UniversalLogParser(BaseLogParser):
    def can_parse(self, raw_logs: str) -> bool:
        return True  # Fallback handles all

    def parse(self, raw_logs: str) -> LogIncident:
        incident = LogIncident(
            framework="generic",
            raw_logs=raw_logs,
            failure_summary="Generic CI/CD workflow failure",
            error_type="ExecutionError",
            exit_code=1,
        )

        # Try to locate any file:line pattern
        match = re.search(r"([a-zA-Z0-9_\-\./]+\.[a-zA-Z0-9]+):(\d+)", raw_logs)
        if match:
            incident.failing_file = match.group(1)
            incident.line_number = int(match.group(2))

        # Check for common error keywords
        for err in ["Error", "Exception", "Fatal", "FAILED", "Panic"]:
            m = re.search(rf"([A-Za-z0-9_]*{err}[A-Za-z0-9_]*):\s*(.+)", raw_logs)
            if m:
                incident.error_type = m.group(1)
                incident.failure_summary = f"{m.group(1)}: {m.group(2)[:120]}"
                break

        lines = raw_logs.strip().splitlines()
        incident.stack_trace = "\n".join(lines[-30:])
        return incident
