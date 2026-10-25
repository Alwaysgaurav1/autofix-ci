import os
from pathlib import Path
from typing import Optional, Dict, List
from pydantic import BaseModel, Field


class RepoContext(BaseModel):
    root_dir: str
    failing_file_path: Optional[str] = None
    file_content: Optional[str] = None
    project_files: List[str] = Field(default_factory=list)
    git_diff: Optional[str] = None


class ContextAgent:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir).resolve()

    def gather_context(self, target_file_hint: Optional[str] = None) -> RepoContext:
        ctx = RepoContext(root_dir=str(self.root_dir))

        # 1. Index top-level and source project files
        all_files = []
        for root, dirs, files in os.walk(self.root_dir):
            # Ignore hidden and build directories
            dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv", ".venv", "dist", "build")]
            for file in files:
                if not file.startswith("."):
                    rel = Path(root, file).relative_to(self.root_dir)
                    all_files.append(str(rel))
        ctx.project_files = all_files[:50]  # First 50 files

        # 2. Locate target file
        resolved_path = None
        if target_file_hint:
            clean_hint = target_file_hint.strip().lstrip("/")
            # Direct check
            direct = self.root_dir / clean_hint
            if direct.is_file():
                resolved_path = direct
            else:
                # Search by basename
                target_name = Path(clean_hint).name
                for f in all_files:
                    if Path(f).name == target_name:
                        resolved_path = self.root_dir / f
                        break

        # If not found yet, inspect first non-test source file
        if not resolved_path:
            for f in all_files:
                if f.endswith((".py", ".ts", ".js", "Dockerfile")) and not f.startswith("test") and "test" not in f:
                    resolved_path = self.root_dir / f
                    break

        if resolved_path and resolved_path.is_file():
            ctx.failing_file_path = str(resolved_path.relative_to(self.root_dir))
            try:
                ctx.file_content = resolved_path.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                ctx.file_content = f"Error reading file: {e}"

        return ctx
