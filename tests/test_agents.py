import pytest
from pathlib import Path
from core.parsers.base import LogIncident
from core.agents.triage_agent import TriageAgent
from core.agents.context_agent import ContextAgent
from core.agents.patch_agent import PatchAgent
from core.client import NebiusLLMClient


def test_triage_agent():
    client = NebiusLLMClient(mock_fallback=True)
    agent = TriageAgent(client=client)
    inc = LogIncident(
        framework="pytest",
        raw_logs="assert 6 == 5 in test_calculator.py",
        failure_summary="assert 6 == 5",
        failing_file="calculator.py",
    )
    report = agent.triage(inc)
    assert report.root_cause != ""
    assert report.failing_file == "calculator.py"


def test_context_agent(tmp_path):
    # Setup test dummy file
    code_file = tmp_path / "math_mod.py"
    code_file.write_text("def sub(a, b): return a - b\n")

    ctx_agent = ContextAgent(str(tmp_path))
    ctx = ctx_agent.gather_context("math_mod.py")
    assert ctx.failing_file_path == "math_mod.py"
    assert "def sub" in (ctx.file_content or "")


def test_patch_agent():
    client = NebiusLLMClient(mock_fallback=True)
    agent = PatchAgent(client=client)
    inc = LogIncident(
        framework="pytest",
        raw_logs="assert add(2, 3) == 5",
        failure_summary="assert 6 == 5",
        failing_file="calculator.py",
    )
    triage = TriageAgent(client=client).triage(inc)

    class DummyContext:
        failing_file_path = "calculator.py"
        file_content = "def add(a, b): return a + b + 1\n"

    patch = agent.generate_patch(triage, DummyContext())
    assert patch.file_path == "calculator.py"
    assert "return a + b" in patch.patched_content
    assert "-" in patch.unified_diff
    assert "+" in patch.unified_diff
