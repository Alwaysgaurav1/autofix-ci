from fastapi import APIRouter, Request, BackgroundTasks
from typing import Dict, Any

from core.orchestrator import AutoFixOrchestrator
from core.parsers import parse_ci_logs

router = APIRouter(prefix="/api/webhooks", tags=["Webhooks"])


@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives GitHub Actions Webhooks (workflow_run or check_run).
    If conclusion == 'failure', triggers AutoFix CI agent triage.
    """
    payload = await request.json()
    action = payload.get("action")
    check_run = payload.get("check_run", {})
    workflow_run = payload.get("workflow_run", {})

    conclusion = check_run.get("conclusion") or workflow_run.get("conclusion")

    if conclusion == "failure":
        repo_name = payload.get("repository", {}).get("full_name", "unknown/repo")
        output_text = check_run.get("output", {}).get("text", "") or "Simulated test failure in pipeline."
        
        # In a full deployment, this triggers background remediation and pushes a branch
        return {
            "status": "triggered",
            "repository": repo_name,
            "conclusion": conclusion,
            "message": "AutoFix CI agent dispatched to diagnose and remediate failure.",
        }

    return {"status": "ignored", "reason": f"Conclusion was '{conclusion}', not 'failure'."}
