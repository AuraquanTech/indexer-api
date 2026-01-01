"""
IndexerAPI Command Line Interface.
"""
import asyncio
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from indexer_api.core.config import settings

app = typer.Typer(
    name="indexer-api",
    help="IndexerAPI - Enterprise File Indexing Service",
    add_completion=True,
)
console = Console()


@app.command()
def serve(
    host: str = typer.Option(settings.host, "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(settings.port, "--port", "-p", help="Port to bind to"),
    workers: int = typer.Option(settings.workers, "--workers", "-w", help="Number of workers"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Enable auto-reload"),
) -> None:
    """Start the API server."""
    import uvicorn

    console.print(
        Panel.fit(
            f"[bold green]Starting IndexerAPI[/]\n"
            f"Host: {host}:{port}\n"
            f"Workers: {workers}\n"
            f"Reload: {reload}",
            title="IndexerAPI",
        )
    )

    uvicorn.run(
        "indexer_api.main:app",
        host=host,
        port=port,
        workers=1 if reload else workers,
        reload=reload,
    )


@app.command()
def worker(
    concurrency: int = typer.Option(4, "--concurrency", "-c", help="Worker concurrency"),
    loglevel: str = typer.Option("info", "--loglevel", "-l", help="Log level"),
) -> None:
    """Start Celery worker."""
    from indexer_api.workers.celery_app import celery_app

    console.print(f"[bold green]Starting Celery worker with concurrency={concurrency}[/]")

    celery_app.worker_main(
        argv=[
            "worker",
            f"--concurrency={concurrency}",
            f"--loglevel={loglevel}",
        ]
    )


@app.command()
def init_db() -> None:
    """Initialize the database tables."""
    from indexer_api.db.base import init_db as _init_db

    async def _run():
        console.print("[bold]Initializing database...[/]")
        await _init_db()
        console.print("[bold green]Database initialized successfully![/]")

    asyncio.run(_run())


@app.command()
def create_user(
    email: str = typer.Option(..., "--email", "-e", help="User email"),
    password: str = typer.Option(..., "--password", "-p", help="User password", hide_input=True),
    org_name: str = typer.Option(..., "--org", "-o", help="Organization name"),
    full_name: Optional[str] = typer.Option(None, "--name", "-n", help="Full name"),
) -> None:
    """Create a new user with an organization."""
    from indexer_api.db.base import get_db_context
    from indexer_api.schemas.auth import UserCreate
    from indexer_api.services.auth import AuthService

    async def _run():
        async with get_db_context() as db:
            auth_service = AuthService(db)
            user_data = UserCreate(
                email=email,
                password=password,
                organization_name=org_name,
                full_name=full_name,
            )
            user = await auth_service.create_user(user_data)

            console.print(
                Panel.fit(
                    f"[bold green]User created successfully![/]\n\n"
                    f"ID: {user.id}\n"
                    f"Email: {user.email}\n"
                    f"Organization: {user.organization.name}\n"
                    f"Role: {user.role}",
                    title="New User",
                )
            )

    try:
        asyncio.run(_run())
    except ValueError as e:
        console.print(f"[bold red]Error:[/] {e}")
        raise typer.Exit(1)


@app.command()
def create_api_key(
    email: str = typer.Option(..., "--email", "-e", help="User email"),
    name: str = typer.Option(..., "--name", "-n", help="API key name"),
    scopes: str = typer.Option("read,write", "--scopes", "-s", help="Comma-separated scopes"),
) -> None:
    """Create an API key for a user."""
    from indexer_api.db.base import get_db_context
    from indexer_api.schemas.auth import APIKeyCreate
    from indexer_api.services.auth import AuthService

    async def _run():
        async with get_db_context() as db:
            auth_service = AuthService(db)
            user = await auth_service.get_user_by_email(email)

            if not user:
                console.print(f"[bold red]User not found:[/] {email}")
                raise typer.Exit(1)

            key_data = APIKeyCreate(
                name=name,
                scopes=scopes.split(","),
            )
            api_key = await auth_service.create_api_key(
                org_id=user.organization_id,
                user_id=user.id,
                key_data=key_data,
            )

            console.print(
                Panel.fit(
                    f"[bold green]API Key created![/]\n\n"
                    f"[bold yellow]Key (save this - shown only once!):[/]\n"
                    f"{api_key.key}\n\n"
                    f"Name: {api_key.name}\n"
                    f"Scopes: {', '.join(api_key.scopes)}",
                    title="New API Key",
                )
            )

    asyncio.run(_run())


@app.command()
def info() -> None:
    """Show application information."""
    table = Table(title="IndexerAPI Configuration")

    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("App Name", settings.app_name)
    table.add_row("Version", settings.app_version)
    table.add_row("Environment", settings.environment)
    table.add_row("Debug", str(settings.debug))
    table.add_row("Database", settings.database_url.split("@")[-1] if "@" in settings.database_url else settings.database_url)
    table.add_row("Redis", settings.redis_url)
    table.add_row("API Prefix", settings.api_prefix)

    console.print(table)


@app.command()
def routes() -> None:
    """List all API routes."""
    from indexer_api.main import app as fastapi_app

    table = Table(title="API Routes")

    table.add_column("Method", style="cyan")
    table.add_column("Path", style="green")
    table.add_column("Name", style="yellow")

    for route in fastapi_app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for method in route.methods:
                if method != "HEAD":
                    table.add_row(method, route.path, route.name or "-")

    console.print(table)


if __name__ == "__main__":
    app()
