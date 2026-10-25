import re
from typing import Optional
from core.parsers.base import BaseLogParser, LogIncident


class NodeNpmLogParser(BaseLogParser):
    def can_parse(self, raw_logs: str) -> bool:
        indicators = ["FAIL ", "npm ERR!", "yarn run", "Jest", "Vitest", "TS2", "error TS"]
        return any(ind in raw_logs for ind in indicators)

    def parse(self, raw_logs: str) -> LogIncident:
        incident = LogIncident(
            framework="jest",
            raw_logs=raw_logs,
            failure_summary="Node.js / Jest test failure",
            error_type="TestFailure",
            exit_code=1,
        )

        # Look for FAIL path/to/file.test.ts
        fail_file_match = re.search(r"FAIL\s+([a-zA-Z0-9_\-\./]+\.(?:ts|js|tsx|jsx))", raw_logs)
        if fail_file_match:
            incident.failing_file = fail_file_match.group(1).strip()

        # Look for TypeScript error: src/index.ts:15:3 - error TS2322: Type '...'
        ts_match = re.search(r"([a-zA-Z0-9_\-\./]+\.(?:ts|tsx)):(\d+):(\d+)\s*-\s*error\s*(TS\d+):\s*(.+)", raw_logs)
        if ts_match:
            incident.framework = "typescript"
            incident.failing_file = ts_match.group(1).strip()
            incident.line_number = int(ts_match.group(2))
            incident.error_type = ts_match.group(4)
            incident.failure_summary = ts_match.group(5).strip()

        # Look for Jest test name: ● SuiteName › test name
        jest_test_match = re.search(r"●\s+(.+?)(?:\n\n|\n\s+at)", raw_logs, re.DOTALL)
        if jest_test_match:
            incident.stack_trace = jest_test_match.group(0).strip()
            first_line = incident.stack_trace.splitlines()[0]
            incident.failure_summary = first_line.replace("●", "").strip()

        return incident
