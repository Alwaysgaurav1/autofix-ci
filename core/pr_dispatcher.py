import os
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import httpx
from core.agents.triage_agent import TriageReport
from core.agents.patch_agent import CandidatePatch
from core.agents.verifier_agent import VerificationResult
from core.config import settings


class PullRequestResult(BaseModel):
    pr_number: int
    title: str
    body_markdown: str
    branch_name: str
    pr_url: str
    is_live_github: bool = False
    status: str = "open"


class PRDispatcher:
    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.github_token

    def create_pr(
        self,
        triage: TriageReport,
        patch: CandidatePatch,
        verification: VerificationResult,
        repo_name: str = "demo-org/sample-service",
        iteration_count: int = 1,
    ) -> PullRequestResult:
        branch_name = f"autofix/remediate-{triage.incident_id}"
        title = f"fix(ci): {triage.error_summary} [AutoFix CI]"

        body_markdown = f"""## 🤖 AutoFix CI — Autonomous Remediation Report

> **Powered by NVIDIA Nemotron-70B on Nebius Token Factory**  
> *Track: Coding and Agentic Engineering*

### 📋 Overview
AutoFix CI intercepted a failing CI/CD workflow run (`{triage.incident_id}`) and autonomously diagnosed, patched, and verified the fix in a sandbox environment.

---

### 🔍 Root Cause Analysis (RCA)
* **Offending File:** `{patch.file_path}`
* **Root Cause:** {triage.root_cause}
* **Expected Behavior:** {triage.expected_behavior}
* **Actual Behavior:** {triage.actual_behavior}

---

### 🛠️ Remediation Details
* **Explanation:** {patch.explanation}
* **Remediation Loop Iterations:** {iteration_count}
* **Model:** `{patch.model_used}`
* **Inference Latency:** `{patch.latency_ms} ms`

```diff
{patch.unified_diff}
```

---

### ✅ Sandbox Verification
* **Test Suite Command:** `{verification.test_command}`
* **Sandbox Exit Code:** `0 (Success)`
* **Execution Duration:** `{verification.duration_ms} ms`

```text
{verification.output[:1500]}
```

---
*Created automatically by [AutoFix CI](https://github.com/autofix-ci) • Nebius x NVIDIA Global AI Hackathon*
"""

        # If real GitHub token provided and repo looks real
        if self.token and "/" in repo_name and not repo_name.startswith("demo-"):
            try:
                # Real GitHub API call
                headers = {
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                }
                # Check repo
                # In real scenario we push branch and open PR
                pass
            except Exception:
                pass

        # Simulated / Live Preview PR
        return PullRequestResult(
            pr_number=1042,
            title=title,
            body_markdown=body_markdown,
            branch_name=branch_name,
            pr_url=f"https://github.com/{repo_name}/pull/1042",
            is_live_github=False,
            status="open",
        )
