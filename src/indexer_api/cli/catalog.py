#!/usr/bin/env python3
"""
Project Catalog CLI

Usage:
    pc search <query>       - Full-text search projects
    pc list                 - List all projects
    pc open <name>          - Open project in VS Code / file manager
    pc health               - Show portfolio health report
    pc scan [paths...]      - Trigger filesystem scan
    pc show <name>          - Show project details
"""
from __future__ import annotations

import os
import subprocess
import time
from typing import List, Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="pc",
    help="Project Catalog CLI - search, open, and manage your projects",
    no_args_is_help=True,
)

console = Console()
API_BASE = os.environ.get("CATALOG_API_URL", "http://localhost:8000/api/v1/catalog")
API_TOKEN = os.environ.get("CATALOG_API_TOKEN", "")


def _get_headers() -> dict:
    """Get auth headers."""
    if API_TOKEN:
        return {"Authorization": f"Bearer {API_TOKEN}"}
    return {}


def _get(endpoint: str, params: dict = None) -> dict:
    """Make GET request to API."""
    try:
        r = httpx.get(
            f"{API_BASE}{endpoint}",
            params=params,
            headers=_get_headers(),
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        raise typer.Exit(1)


def _post(endpoint: str, data: dict) -> dict:
    """Make POST request to API."""
    try:
        r = httpx.post(
            f"{API_BASE}{endpoint}",
            json=data,
            headers=_get_headers(),
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        console.print(f"[red]Error: {e.response.status_code} - {e.response.text}[/red]")
        raise typer.Exit(1)
    except httpx.RequestError as e:
        console.print(f"[red]Connection error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    limit: int = typer.Option(10, "--limit", "-n", help="Max results"),
):
    """Full-text search across all projects."""
    data = _get("/search", {"q": query, "limit": limit})
    results = data.get("results", [])

    if not results:
        console.print("[yellow]No projects found.[/yellow]")
        raise typer.Exit(0)

    console.print(f"\n[green]Found {len(results)} project(s):[/green]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("#", style="dim", width=3)
    table.add_column("Name", style="bold")
    table.add_column("Lifecycle")
    table.add_column("Languages")
    table.add_column("Path", style="dim")

    for i, p in enumerate(results, 1):
        name = p.get("title") or p.get("name", "?")
        lifecycle = p.get("lifecycle", "?")
        langs = ", ".join(p.get("languages") or [])[:30] or "-"
        path = p.get("path", "")[:50]

        lifecycle_color = {
            "active": "green",
            "maintenance": "yellow",
            "deprecated": "red",
            "archived": "dim",
        }.get(lifecycle, "white")

        table.add_row(str(i), name, f"[{lifecycle_color}]{lifecycle}[/{lifecycle_color}]", langs, path)

    console.print(table)


@app.command("list")
def list_projects(
    lifecycle: Optional[str] = typer.Option(None, "--lifecycle", "-l", help="Filter by lifecycle"),
    language: Optional[str] = typer.Option(None, "--lang", help="Filter by language"),
    project_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by type"),
    limit: int = typer.Option(50, "--limit", "-n"),
):
    """List all cataloged projects."""
    params = {"per_page": limit}
    if lifecycle:
        params["lifecycle"] = lifecycle
    if language:
        params["language"] = language
    if project_type:
        params["type"] = project_type

    data = _get("/projects", params)
    items = data.get("items", [])
    total = data.get("total", 0)

    console.print(f"\n[bold]Projects ({len(items)}/{total}):[/bold]\n")

    for p in items:
        name = p.get("name")
        lifecycle = p.get("lifecycle", "?")
        icon = {"active": "[green]●[/green]", "maintenance": "[yellow]○[/yellow]",
                "deprecated": "[red]◌[/red]", "archived": "[dim]◦[/dim]"}.get(lifecycle, "?")
        console.print(f"  {icon} {name}")

    console.print()


@app.command()
def show(name: str = typer.Argument(..., help="Project name or ID")):
    """Show detailed project info."""
    # Try by ID first, then search by name
    try:
        data = _get(f"/projects/{name}")
    except typer.Exit:
        # Might be a name, search for it
        search_data = _get("/search", {"q": name, "limit": 1})
        results = search_data.get("results", [])
        if not results:
            console.print(f"[red]Project '{name}' not found.[/red]")
            raise typer.Exit(1)
        data = results[0]

    console.print(f"\n[bold]{data.get('title') or data.get('name')}[/bold]")
    console.print(f"  [dim]Name:[/dim]       {data.get('name')}")
    console.print(f"  [dim]Path:[/dim]       {data.get('path')}")
    console.print(f"  [dim]Type:[/dim]       {data.get('type')}")
    console.print(f"  [dim]Lifecycle:[/dim]  {data.get('lifecycle')}")
    console.print(f"  [dim]Languages:[/dim]  {', '.join(data.get('languages') or []) or '-'}")
    console.print(f"  [dim]Frameworks:[/dim] {', '.join(data.get('frameworks') or []) or '-'}")

    if data.get("repository_url"):
        console.print(f"  [dim]Repo:[/dim]       {data.get('repository_url')}")
    if data.get("license_spdx"):
        console.print(f"  [dim]License:[/dim]    {data.get('license_spdx')}")
    if data.get("health_score"):
        console.print(f"  [dim]Health:[/dim]     {data.get('health_score'):.1f}")
    if data.get("loc_total"):
        console.print(f"  [dim]LOC:[/dim]        {data.get('loc_total'):,}")
    if data.get("description"):
        console.print(f"\n  {data.get('description')[:200]}")

    console.print()


@app.command("open")
def open_project(
    name: str = typer.Argument(..., help="Project name"),
    editor: str = typer.Option("code", "--editor", "-e", help="Editor command (code, cursor, vim, etc.)"),
):
    """Open project in VS Code or specified editor."""
    # Find project
    search_data = _get("/search", {"q": name, "limit": 5})
    results = search_data.get("results", [])

    if not results:
        console.print(f"[red]Project '{name}' not found.[/red]")
        raise typer.Exit(1)

    # Exact match or first result
    project = None
    for r in results:
        if r.get("name") == name:
            project = r
            break
    project = project or results[0]

    path = project.get("path")
    if not path or not os.path.exists(path):
        console.print(f"[red]Path not found: {path}[/red]")
        raise typer.Exit(1)

    console.print(f"[green]Opening {project.get('name')} in {editor}...[/green]")

    try:
        subprocess.run([editor, path], check=True)
    except FileNotFoundError:
        console.print(f"[red]Editor '{editor}' not found. Try: --editor vim[/red]")
        raise typer.Exit(1)


@app.command()
def health():
    """Show portfolio health report."""
    data = _get("/health-report")

    console.print()
    console.print("[bold]" + "═" * 50 + "[/bold]")
    console.print("[bold]  PROJECT CATALOG HEALTH REPORT[/bold]")
    console.print(f"  [dim]Generated: {data.get('generated_at', '')[:19]}[/dim]")
    console.print("[bold]" + "═" * 50 + "[/bold]")
    console.print()

    console.print(f"  [bold]Total Projects:[/bold]    {data.get('total_projects', 0)}")
    console.print(f"  [bold]Recently Updated:[/bold]  {data.get('recently_updated', 0)} [dim](7 days)[/dim]")
    console.print(f"  [bold]Stale:[/bold]             {data.get('stale_count', 0)} [dim](30+ days)[/dim]")

    avg = data.get("avg_health_score")
    if avg:
        color = "green" if avg >= 70 else "yellow" if avg >= 50 else "red"
        console.print(f"  [bold]Avg Health Score:[/bold]  [{color}]{avg}[/{color}]")

    total_loc = data.get("total_loc")
    if total_loc:
        console.print(f"  [bold]Total LOC:[/bold]         {total_loc:,}")

    console.print(f"\n  [bold]By Lifecycle:[/bold]")
    for lc, count in (data.get("by_lifecycle") or {}).items():
        icon = {"active": "[green]●[/green]", "maintenance": "[yellow]○[/yellow]",
                "deprecated": "[red]◌[/red]", "archived": "[dim]◦[/dim]"}.get(lc, "?")
        console.print(f"    {icon} {lc}: {count}")

    console.print(f"\n  [bold]By Language:[/bold]")
    for lang, count in sorted((data.get("by_language") or {}).items(), key=lambda x: -x[1])[:10]:
        console.print(f"    {lang}: {count}")

    console.print()


@app.command()
def scan(
    paths: Optional[List[str]] = typer.Argument(None, help="Paths to scan"),
    max_depth: int = typer.Option(5, "--depth", "-d"),
    wait: bool = typer.Option(False, "--wait", "-w", help="Wait for job completion"),
):
    """Trigger filesystem scan for new/changed projects."""
    payload = {"paths": paths or [], "max_depth": max_depth, "recursive": True}
    data = _post("/scan", payload)

    job_id = data.get("job_id")
    console.print(f"[green]Scan job enqueued: {job_id}[/green]")

    if wait:
        console.print("[dim]Waiting for completion...[/dim]")
        while True:
            status_data = _get(f"/jobs/{job_id}")
            s = status_data.get("status")
            if s in ("succeeded", "failed", "completed"):
                color = "green" if s in ("succeeded", "completed") else "red"
                console.print(f"[{color}]Job {s}.[/{color}]")
                if status_data.get("runs"):
                    last = status_data["runs"][0]
                    if last.get("result"):
                        console.print(f"  Discovered: {last['result'].get('discovered', '?')} projects")
                        console.print(f"  Enqueued:   {last['result'].get('enqueued', '?')} refresh jobs")
                break
            console.print(f"  [dim]Status: {s} (attempts: {status_data.get('attempts')})[/dim]")
            time.sleep(2)


@app.command()
def job(job_id: str = typer.Argument(..., help="Job ID to check")):
    """Check job status."""
    data = _get(f"/jobs/{job_id}")

    console.print(f"\n[bold]Job: {data.get('job_id')}[/bold]")
    console.print(f"  [dim]Type:[/dim]     {data.get('job_type')}")

    status = data.get("status")
    color = {"succeeded": "green", "completed": "green", "failed": "red", "running": "yellow"}.get(status, "white")
    console.print(f"  [dim]Status:[/dim]   [{color}]{status}[/{color}]")
    console.print(f"  [dim]Attempts:[/dim] {data.get('attempts')}/{data.get('max_attempts')}")
    console.print(f"  [dim]Created:[/dim]  {data.get('created_at', '')[:19]}")

    if data.get("last_error"):
        console.print(f"  [red]Error:[/red]    {data['last_error'].get('message', '?')}")

    runs = data.get("runs", [])
    if runs:
        console.print(f"\n  [bold]Recent runs:[/bold]")
        for r in runs[:3]:
            console.print(f"    - {r.get('status')} at {r.get('started_at', '')[:19]}")

    console.print()


def main():
    """Entry point."""
    app()


if __name__ == "__main__":
    main()
