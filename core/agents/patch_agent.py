import difflib
import json
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from core.agents.triage_agent import TriageReport
from core.agents.context_agent import RepoContext
from core.client import NebiusLLMClient, llm_client


class CandidatePatch(BaseModel):
    file_path: str
    original_content: str
    patched_content: str
    unified_diff: str
    explanation: str
    tokens_used: int = 0
    model_used: str = ""
    latency_ms: float = 0.0


PATCH_SYSTEM_PROMPT = """You are an elite Autonomous Code Generation and Repair Engineer powered by NVIDIA Nemotron on Nebius Token Factory.
Your task is to fix the code that caused a CI/CD or test pipeline failure.

Guidelines:
1. Make surgical, minimal edits. Do not rewrite unaffected functions or erase comments.
2. Ensure types, imports, and syntax are 100% valid.
3. Respond ONLY in valid JSON matching this schema:
{
  "explanation": "Clear explanation of what was fixed and why",
  "file_path": "relative/path/to/remediated_file.ext",
  "patched_content": "THE ENTIRE NEW FILE CONTENT WITH FIX APPLIED"
}
"""


class PatchAgent:
    def __init__(self, client: Optional[NebiusLLMClient] = None):
        self.client = client or llm_client

    def generate_patch(
        self,
        triage: TriageReport,
        context: RepoContext,
        feedback: Optional[str] = None,
    ) -> CandidatePatch:
        file_path = context.failing_file_path or triage.failing_file or "unknown"
        original_code = context.file_content or ""

        user_prompt = f"""Fix the failing CI/CD failure:
Target File: {file_path}
Root Cause: {triage.root_cause}
Error Summary: {triage.error_summary}
Expected Behavior: {triage.expected_behavior}
Actual Behavior: {triage.actual_behavior}

--- ORIGINAL FILE CONTENT ---
{original_code}
"""
        if feedback:
            user_prompt += f"""
--- PREVIOUS RUN VERIFICATION FEEDBACK ---
The previous patch failed with this error:
{feedback}
Please adjust the fix to solve this issue as well.
"""

        messages = [
            {"role": "system", "content": PATCH_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        completion = self.client.complete(messages, temperature=0.15)
        raw_text = completion.get("content", "").strip()

        patched_content = original_code
        explanation = "Automated fix synthesized by NVIDIA Nemotron"

        try:
            if "```" in raw_text:
                json_part = raw_text.split("```json")[-1].split("```")[0].strip()
                if not json_part:
                    json_part = raw_text.split("```")[1].strip()
            else:
                json_part = raw_text

            data = json.loads(json_part)
            patched_content = data.get("patched_content", original_code)
            explanation = data.get("explanation", explanation)
            if data.get("file_path"):
                file_path = data.get("file_path")
        except Exception:
            # If model returned pure code without JSON, use it
            if raw_text.startswith("def ") or raw_text.startswith("import ") or raw_text.startswith("export "):
                patched_content = raw_text

        # Compute unified diff
        diff_lines = list(
            difflib.unified_diff(
                original_code.splitlines(keepends=True),
                patched_content.splitlines(keepends=True),
                fromfile=f"a/{file_path}",
                tofile=f"b/{file_path}",
            )
        )
        unified_diff = "".join(diff_lines)

        return CandidatePatch(
            file_path=file_path,
            original_content=original_code,
            patched_content=patched_content,
            unified_diff=unified_diff,
            explanation=explanation,
            tokens_used=completion.get("prompt_tokens", 0) + completion.get("completion_tokens", 0),
            model_used=completion.get("model", ""),
            latency_ms=completion.get("latency_ms", 0.0),
        )
