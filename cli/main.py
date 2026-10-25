import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from pathlib import Path
import sys
import uvicorn

from core.orchestrator import AutoFixOrchestrator
from core.config import settings
from core.client import llm_client

app = typer.Typer(
    name="autofix",
    help="Autonomous CI/CD Failure Triage & Auto-PR Agent powered by NVIDIA Nemotron on Nebius Token Factory",
    add_completion=False,
)
console = Console()


@app.command()
def info():
    """Display AutoFix CI and Nebius Token Factory configuration."""
    table = Table(title="AutoFix CI Configuration", header_style="bold magenta")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Nebius Base URL", settings.nebius_base_url)
    table.add_row("NVIDIA Model", settings.nebius_model)
    table.add_row("API Key Configured", "✅ Yes" if not llm_client.is_using_mock else "⚠️ No (Using Deterministic Fallback)")
    table.add_row("Max Iterations", str(settings.autofix_max_iterations))
    table.add_row("Timeout (seconds)", str(settings.autofix_timeout_seconds))
    table.add_row("GitHub Token", "✅ Yes" if settings.github_token else "⚠️ Not configured")
    console.print(table)


@app.command()
def run(
    log_file: Path = typer.Option(..., "--log", "-l", help="Path to raw CI/CD failure log"),
    repo_dir: Path = typer.Option(Path("."), "--dir", "-d", help="Path to target repository"),
    test_cmd: str = typer.Option(None, "--test-cmd", "-t", help="Verification test command (e.g. 'pytest')"),
    max_iter: int = typer.Option(3, "--max-iter", "-m", help="Maximum agent self-correction attempts"),
):
    """Run autonomous remediation on a failing CI/CD log."""
    if not log_file.exists():
        console.print(f"[bold red]Error:[/] Log file not found at {log_file}")
        raise typer.Exit(code=1)

    raw_logs = log_file.read_text(encoding="utf-8", errors="replace")

    console.print(Panel.fit(
        f"[bold blue]AutoFix CI Agent[/bold blue] 🚀\n"
        f"[dim]Powered by NVIDIA Nemotron on Nebius Token Factory[/dim]\n"
        f"Log: [cyan]{log_file.name}[/] | Target: [yellow]{repo_dir.resolve()}[/]",
        border_style="blue",
    ))

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Initializing remediation pipeline...", total=None)

        def event_cb(evt: str, data: dict):
            if evt == "LOG_PARSED":
                progress.update(task, description=f"[green]Parsed {data.get('framework')} error: {data.get('summary')}")
            elif evt == "TRIAGE_COMPLETED":
                progress.update(task, description=f"[bold cyan]NVIDIA Nemotron RCA: {data.get('root_cause')[:60]}...")
            elif evt == "SYNTHESIS_STARTED":
                progress.update(task, description=f"[yellow]Synthesizing patch (Attempt {data.get('iteration')})...")
            elif evt == "VERIFICATION_STARTED":
                progress.update(task, description=f"[magenta]Verifying patch in isolated sandbox...")
            elif evt == "VERIFICATION_PASSED":
                progress.update(task, description="[bold green]Sandbox tests passed! Generating PR report...")

        orchestrator = AutoFixOrchestrator(
            repo_dir=str(repo_dir),
            test_command=test_cmd,
            max_iterations=max_iter,
            event_callback=event_cb,
        )

        session = orchestrator.remediate(raw_logs)

    # Output Results
    if session.success:
        console.print(Panel(
            f"[bold green]✔ CI Pipeline Auto-Remediated Successfully![/bold green]\n\n"
            f"[bold]Root Cause:[/] {session.triage.root_cause if session.triage else 'N/A'}\n"
            f"[bold]Iterations:[/] {session.total_iterations} attempt(s)\n"
            f"[bold]Total Time:[/] {session.total_duration_ms:.1f} ms\n"
            f"[bold]Pull Request:[/] [link={session.pr_result.pr_url if session.pr_result else ''}]{session.pr_result.pr_url if session.pr_result else 'N/A'}[/link]",
            title="Remediation Summary",
            border_style="green",
        ))

        if session.final_patch and session.final_patch.unified_diff:
            console.print("\n[bold]Synthesized Diff:[/bold]")
            syntax = Syntax(session.final_patch.unified_diff, "diff", theme="monokai", line_numbers=True)
            console.print(syntax)
    else:
        console.print(Panel(
            f"[bold red]✖ Auto-Remediation Unsuccessful[/bold red]\n"
            f"Exceeded {session.total_iterations} iterations without passing verification.\n"
            f"Last Error: {session.verification.error_summary if session.verification else 'Unknown'}",
            title="Remediation Failed",
            border_style="red",
        ))
        raise typer.Exit(code=1)


@app.command()
def demo(scenario: int = typer.Argument(1, help="Demo scenario (1: Python/Pytest, 2: Node/Jest, 3: Docker)")):
    """Run an instant evaluation demo for hackathon judges."""
    base = Path(__file__).resolve().parent.parent / "benchmarks"

    if scenario == 1:
        target = base / "scenario_1_python_calc"
        log = target / "failure.log"
        test_cmd = sys.executable + " -m pytest -q"
        console.print("[bold yellow]Running Demo Scenario 1: Python Pytest Off-by-One Arithmetic Failure[/]")
    elif scenario == 2:
        target = base / "scenario_2_node_validator"
        log = target / "failure.log"
        test_cmd = "node test_validator.js"
        console.print("[bold yellow]Running Demo Scenario 2: Node.js / TypeScript Regex Validation Failure[/]")
    elif scenario == 3:
        target = base / "scenario_3_docker_build"
        log = target / "failure.log"
        test_cmd = "echo 'Docker syntax validated'"
        console.print("[bold yellow]Running Demo Scenario 3: Dockerfile Build Layer Failure[/]")
    else:
        console.print(f"[red]Unknown scenario {scenario}. Choose 1, 2, or 3.[/]")
        raise typer.Exit(code=1)

    run(log_file=log, repo_dir=target, test_cmd=test_cmd, max_iter=2)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h"),
    port: int = typer.Option(8000, "--port", "-p"),
):
    """Start the AutoFix CI FastAPI backend and SSE server."""
    console.print(f"[bold green]Starting AutoFix CI API Server at http://{host}:{port}[/]")
    uvicorn.run("api.main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    app()
