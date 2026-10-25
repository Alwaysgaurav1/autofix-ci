from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import json
from core.parsers.base import LogIncident
from core.client import NebiusLLMClient, llm_client


class TriageReport(BaseModel):
    incident_id: str
    root_cause: str
    error_summary: str
    failing_file: str
    failing_line: Optional[int] = None
    expected_behavior: str
    actual_behavior: str
    suggested_action: str
    raw_response: Dict[str, Any] = Field(default_factory=dict)


TRIAGE_SYSTEM_PROMPT = """You are an elite Autonomous SRE and DevOps Principal Engineer using NVIDIA Nemotron on Nebius Token Factory.
Your job is to analyze broken CI/CD logs, stack traces, and test execution output.
You must pinpoint the exact root cause, identify the primary offending file, and describe why the failure occurred.

Respond STRICTLY in valid JSON matching this schema:
{
  "root_cause": "concise description of why it failed",
  "error_summary": "1-sentence summary for the PR title",
  "failing_file": "path/to/failing_file.ext",
  "failing_line": 123,
  "expected_behavior": "what should have happened",
  "actual_behavior": "what actually happened",
  "suggested_action": "concrete steps to fix the code"
}
"""


class TriageAgent:
    def __init__(self, client: Optional[NebiusLLMClient] = None):
        self.client = client or llm_client

    def triage(self, incident: LogIncident) -> TriageReport:
        user_prompt = f"""Analyze this CI/CD failure:
Framework: {incident.framework}
Detected Error Type: {incident.error_type}
Failure Summary: {incident.failure_summary}
Failing File: {incident.failing_file or 'Unknown'}
Line Number: {incident.line_number or 'Unknown'}

--- STACK TRACE & LOGS ---
{incident.stack_trace or incident.raw_logs[:3000]}
"""

        messages = [
            {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        completion = self.client.complete(messages, temperature=0.1)
        raw_text = completion.get("content", "").strip()

        # Extract JSON from response
        try:
            # Handle potential markdown code fencing ```json ... ```
            if "```" in raw_text:
                json_part = raw_text.split("```json")[-1].split("```")[0].strip()
                if not json_part:
                    json_part = raw_text.split("```")[1].strip()
            else:
                json_part = raw_text

            data = json.loads(json_part)
            return TriageReport(
                incident_id=incident.id,
                root_cause=data.get("root_cause", incident.failure_summary),
                error_summary=data.get("error_summary", incident.failure_summary),
                failing_file=data.get("failing_file", incident.failing_file or "unknown"),
                failing_line=data.get("failing_line", incident.line_number),
                expected_behavior=data.get("expected_behavior", "Test to pass with code 0"),
                actual_behavior=data.get("actual_behavior", incident.failure_summary),
                suggested_action=data.get("suggested_action", "Repair logic error in source file"),
                raw_response=completion,
            )
        except Exception:
            # Fallback if json parsing fails
            return TriageReport(
                incident_id=incident.id,
                root_cause=incident.failure_summary,
                error_summary=f"Fix {incident.error_type} in {incident.failing_file or 'source'}",
                failing_file=incident.failing_file or "unknown",
                failing_line=incident.line_number,
                expected_behavior="Code execution without runtime or assertion exceptions",
                actual_behavior=incident.failure_summary,
                suggested_action="Refactor failing block to handle edge case",
                raw_response=completion,
            )
