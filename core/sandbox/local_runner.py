import subprocess
import shutil
import tempfile
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ExecutionResult(BaseModel):
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    timed_out: bool = False


class LocalSandboxRunner:
    def __init__(self, base_repo_dir: str, timeout_seconds: int = 30):
        self.base_repo_dir = Path(base_repo_dir).resolve()
        self.timeout_seconds = timeout_seconds
        self.sandbox_dir: Optional[Path] = None

    def create_sandbox(self) -> Path:
        """Copies the project into an isolated temporary directory."""
        temp_dir = tempfile.mkdtemp(prefix="autofix_sandbox_")
        self.sandbox_dir = Path(temp_dir)

        # Copy files excluding hidden / cache
        def ignore_patterns(path, names):
            ignored = set()
            for name in names:
                if name in ("node_modules", ".git", ".venv", "__pycache__", ".pytest_cache", ".next"):
                    ignored.add(name)
            return ignored

        shutil.copytree(self.base_repo_dir, self.sandbox_dir, dirs_exist_ok=True, ignore=ignore_patterns)
        return self.sandbox_dir

    def apply_patch(self, rel_path: str, new_content: str):
        """Writes the remediated content to the relative path within the sandbox."""
        if not self.sandbox_dir:
            raise RuntimeError("Sandbox has not been created yet.")

        target_file = self.sandbox_dir / rel_path
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text(new_content, encoding="utf-8")

    def run_command(self, command: str, env: Optional[Dict[str, str]] = None) -> ExecutionResult:
        """Executes a command inside the sandbox."""
        cwd = self.sandbox_dir or self.base_repo_dir
        start = time.time()
        
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        try:
            process = subprocess.run(
                command,
                cwd=str(cwd),
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                env=merged_env,
            )
            duration_ms = (time.time() - start) * 1000
            return ExecutionResult(
                command=command,
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
                duration_ms=round(duration_ms, 2),
                timed_out=False,
            )
        except subprocess.TimeoutExpired as e:
            duration_ms = (time.time() - start) * 1000
            return ExecutionResult(
                command=command,
                exit_code=124,
                stdout=e.stdout or "" if isinstance(e.stdout, str) else "",
                stderr="Execution timed out after " + str(self.timeout_seconds) + "s",
                duration_ms=round(duration_ms, 2),
                timed_out=True,
            )

    def cleanup(self):
        """Removes the temporary sandbox directory."""
        if self.sandbox_dir and self.sandbox_dir.exists():
            try:
                shutil.rmtree(self.sandbox_dir)
            except Exception:
                pass
            self.sandbox_dir = None
