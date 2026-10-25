from typing import Optional
from pydantic import BaseModel
from core.agents.patch_agent import CandidatePatch
from core.sandbox.local_runner import LocalSandboxRunner, ExecutionResult


class VerificationResult(BaseModel):
    passed: bool
    exit_code: int
    test_command: str
    output: str
    duration_ms: float
    error_summary: Optional[str] = None


class VerifierAgent:
    def __init__(self, sandbox_runner: LocalSandboxRunner):
        self.runner = sandbox_runner

    def verify(self, patch: CandidatePatch, test_command: Optional[str] = None) -> VerificationResult:
        # 1. Apply patch to sandbox
        self.runner.apply_patch(patch.file_path, patch.patched_content)

        # 2. Determine test command
        cmd = test_command or self._infer_test_command(patch.file_path)

        # 3. Execute
        res = self.runner.run_command(cmd)

        passed = (res.exit_code == 0)
        output = res.stdout + ("\n" + res.stderr if res.stderr else "")

        return VerificationResult(
            passed=passed,
            exit_code=res.exit_code,
            test_command=cmd,
            output=output.strip(),
            duration_ms=res.duration_ms,
            error_summary=None if passed else output[-800:],
        )

    def _infer_test_command(self, file_path: str) -> str:
        if file_path.endswith(".py"):
            return "pytest -q"
        elif file_path.endswith((".ts", ".js")):
            return "npm test"
        return "pytest"
