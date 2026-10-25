import time
from typing import Optional, Callable, Dict, Any, List
from pydantic import BaseModel, Field

from core.parsers import parse_ci_logs, LogIncident
from core.agents.triage_agent import TriageAgent, TriageReport
from core.agents.context_agent import ContextAgent, RepoContext
from core.agents.patch_agent import PatchAgent, CandidatePatch
from core.agents.verifier_agent import VerifierAgent, VerificationResult
from core.sandbox.local_runner import LocalSandboxRunner
from core.pr_dispatcher import PRDispatcher, PullRequestResult
from core.config import settings


class RemediationSession(BaseModel):
    session_id: str
    incident: LogIncident
    triage: Optional[TriageReport] = None
    final_patch: Optional[CandidatePatch] = None
    verification: Optional[VerificationResult] = None
    pr_result: Optional[PullRequestResult] = None
    total_iterations: int = 0
    success: bool = False
    total_duration_ms: float = 0.0
    timeline: List[Dict[str, Any]] = Field(default_factory=list)


class AutoFixOrchestrator:
    def __init__(
        self,
        repo_dir: str,
        test_command: Optional[str] = None,
        max_iterations: int = settings.autofix_max_iterations,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        self.repo_dir = repo_dir
        self.test_command = test_command
        self.max_iterations = max_iterations
        self.event_callback = event_callback or (lambda evt, data: None)

    def _emit(self, event_type: str, data: Dict[str, Any]):
        self.event_callback(event_type, data)

    def remediate(self, raw_logs: str) -> RemediationSession:
        start_time = time.time()
        timeline: List[Dict[str, Any]] = []

        def log_step(name: str, details: Dict[str, Any]):
            step_obj = {"step": name, "timestamp": time.time(), "details": details}
            timeline.append(step_obj)
            self._emit(name, details)

        # 1. Parse CI Logs
        log_step("LOG_INGESTION_STARTED", {"msg": "Parsing raw CI failure logs..."})
        incident = parse_ci_logs(raw_logs)
        log_step("LOG_PARSED", {
            "incident_id": incident.id,
            "framework": incident.framework,
            "error_type": incident.error_type,
            "summary": incident.failure_summary,
            "failing_file": incident.failing_file,
        })

        session = RemediationSession(
            session_id=incident.id,
            incident=incident,
            timeline=timeline,
        )

        # 2. Triage with NVIDIA Nemotron
        log_step("TRIAGE_STARTED", {"msg": "Invoking NVIDIA Nemotron for root-cause analysis on Nebius Token Factory..."})
        triage_agent = TriageAgent()
        triage = triage_agent.triage(incident)
        session.triage = triage
        log_step("TRIAGE_COMPLETED", {
            "root_cause": triage.root_cause,
            "failing_file": triage.failing_file,
            "suggested_action": triage.suggested_action,
        })

        # 3. Context Inspection
        log_step("CONTEXT_INSPECTION_STARTED", {"msg": "Inspecting repository structure and target source file..."})
        ctx_agent = ContextAgent(self.repo_dir)
        context = ctx_agent.gather_context(triage.failing_file)
        log_step("CONTEXT_GATHERED", {
            "resolved_file": context.failing_file_path,
            "file_size_bytes": len(context.file_content or ""),
            "indexed_files_count": len(context.project_files),
        })

        # 4. Setup Isolated Sandbox
        log_step("SANDBOX_INITIALIZATION", {"msg": "Creating isolated verification sandbox..."})
        runner = LocalSandboxRunner(self.repo_dir, timeout_seconds=settings.autofix_timeout_seconds)
        sandbox_path = runner.create_sandbox()
        verifier = VerifierAgent(runner)

        # 5. Iterative Patch & Verify Loop (Agent Self-Correction)
        patch_agent = PatchAgent()
        feedback: Optional[str] = None
        final_patch: Optional[CandidatePatch] = None
        last_verification: Optional[VerificationResult] = None
        success = False

        try:
            for iteration in range(1, self.max_iterations + 1):
                session.total_iterations = iteration
                log_step("SYNTHESIS_STARTED", {
                    "iteration": iteration,
                    "max_iterations": self.max_iterations,
                    "msg": f"NVIDIA Nemotron synthesizing code patch (Attempt {iteration}/{self.max_iterations})...",
                })

                patch = patch_agent.generate_patch(triage, context, feedback=feedback)
                final_patch = patch
                session.final_patch = patch

                log_step("PATCH_SYNTHESIZED", {
                    "iteration": iteration,
                    "diff": patch.unified_diff,
                    "explanation": patch.explanation,
                    "model": patch.model_used,
                    "latency_ms": patch.latency_ms,
                })

                # Verify in Sandbox
                log_step("VERIFICATION_STARTED", {
                    "iteration": iteration,
                    "msg": f"Running verification suite inside sandbox: {self.test_command or 'auto-inferred'}...",
                })
                verification = verifier.verify(patch, test_command=self.test_command)
                last_verification = verification
                session.verification = verification

                if verification.passed:
                    success = True
                    log_step("VERIFICATION_PASSED", {
                        "iteration": iteration,
                        "exit_code": 0,
                        "duration_ms": verification.duration_ms,
                        "output": verification.output[:300],
                    })
                    break
                else:
                    feedback = verification.error_summary
                    log_step("VERIFICATION_FAILED", {
                        "iteration": iteration,
                        "exit_code": verification.exit_code,
                        "error_summary": verification.error_summary,
                        "msg": "Test suite still failing. Passing error trace back to Nemotron for self-correction.",
                    })

        finally:
            runner.cleanup()

        session.success = success

        # 6. Dispatch Pull Request
        if final_patch and last_verification:
            log_step("PR_DISPATCH_STARTED", {"msg": "Generating automated Pull Request report..."})
            dispatcher = PRDispatcher()
            pr = dispatcher.create_pr(
                triage=triage,
                patch=final_patch,
                verification=last_verification,
                iteration_count=session.total_iterations,
            )
            session.pr_result = pr
            log_step("PR_DISPATCHED", {
                "pr_number": pr.pr_number,
                "title": pr.title,
                "url": pr.pr_url,
                "branch": pr.branch_name,
            })

        session.total_duration_ms = round((time.time() - start_time) * 1000, 2)
        log_step("REMEDIATION_COMPLETE", {
            "success": session.success,
            "duration_ms": session.total_duration_ms,
            "iterations": session.total_iterations,
        })

        return session
