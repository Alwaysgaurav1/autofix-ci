import re
from typing import Optional
from core.parsers.base import BaseLogParser, LogIncident


class PytestLogParser(BaseLogParser):
    def can_parse(self, raw_logs: str) -> bool:
        indicators = ["pytest", "FAILED ", "=== FAILURES ===", "=== SHORT test summary info ==="]
        return any(ind in raw_logs for ind in indicators)

    def parse(self, raw_logs: str) -> LogIncident:
        incident = LogIncident(
            framework="pytest",
            raw_logs=raw_logs,
            failure_summary="Pytest test suite failure",
            error_type="AssertionError",
            exit_code=1,
        )

        # 1. Look for FAILED test summary: FAILED tests/test_math.py::test_division - ZeroDivisionError
        fail_summary_match = re.search(r"FAILED\s+([^\s:]+)::([^\s\-]+)(?:\s+-\s+(.+))?", raw_logs)
        if fail_summary_match:
            incident.failing_file = fail_summary_match.group(1)
            incident.failing_test_name = fail_summary_match.group(2)
            if fail_summary_match.group(3):
                incident.failure_summary = fail_summary_match.group(3).strip()

        # 2. Extract file and line number: e.g. tests/test_calculator.py:24: AssertionError
        file_line_match = re.search(r"([a-zA-Z0-9_\-\./]+\.py):(\d+):\s*([a-zA-Z0-9_]+Error|AssertionError|Exception)", raw_logs)
        if file_line_match:
            incident.failing_file = file_line_match.group(1)
            incident.line_number = int(file_line_match.group(2))
            incident.error_type = file_line_match.group(3)

        # 3. Extract failure block / stack trace
        failure_block_match = re.search(r"_{10,}\s*(.+?)\s*_{10,}(.+?)(?=(?:_{10,}|={10,}|$))", raw_logs, re.DOTALL)
        if failure_block_match:
            incident.stack_trace = failure_block_match.group(0).strip()
        else:
            # Fallback: extract lines around "E   "
            error_lines = [line for line in raw_logs.splitlines() if line.startswith("E   ") or line.startswith(">   ")]
            incident.stack_trace = "\n".join(error_lines) if error_lines else raw_logs[-1500:]

        if incident.failing_test_name:
            incident.failure_summary = f"{incident.error_type} in {incident.failing_test_name}"

        return incident
