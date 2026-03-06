"""CLI commands for triggering and querying builds."""

import click
import requests
from rich.console import Console
from rich.table import Table

console = Console()


def _safe_error(resp):
    """Extract error message from a response, handling non-JSON bodies."""
    try:
        return resp.json().get("error", resp.text)
    except requests.exceptions.JSONDecodeError:
        return resp.text or f"HTTP {resp.status_code}"


@click.group()
def builds():
    """Manage builds."""


@builds.command("trigger")
@click.option("--app-id", required=True, type=int, help="Application ID to build")
@click.option("--branch", default="main", help="Branch to build (default: main)")
@click.option("--commit", default=None, help="Commit SHA (optional)")
@click.pass_context
def trigger_build(ctx, app_id, branch, commit):
    """Trigger a new build for an application."""
    payload = {"app_id": app_id, "branch": branch}
    if commit:
        payload["commit_sha"] = commit

    resp = requests.post(
        f"{ctx.obj['api_url']}/api/builds",
        json=payload,
        timeout=10,
    )
    if resp.status_code == 201:
        build = resp.json()
        console.print(
            f"[green]Build #{build['id']} triggered for "
            f"'{build['app_name']}' on branch '{build['branch']}'[/green]"
        )
        console.print(f"  Status: {build['status']}")
    else:
        console.print(f"[red]Error:[/red] {_safe_error(resp)}")


@builds.command("status")
@click.option("--id", "build_id", required=True, type=int, help="Build ID")
@click.pass_context
def build_status(ctx, build_id):
    """Check the status of a build."""
    resp = requests.get(f"{ctx.obj['api_url']}/api/builds/{build_id}", timeout=10)
    if resp.status_code != 200:
        console.print(f"[red]Error:[/red] {_safe_error(resp)}")
        return

    build = resp.json()
    console.print(f"[bold]Build #{build['id']}[/bold]")
    console.print(f"  App:      {build['app_name']}")
    console.print(f"  Branch:   {build['branch']}")
    console.print(f"  Status:   {build['status']}")
    console.print(f"  Commit:   {build['commit_sha'] or 'N/A'}")
    console.print(f"  Started:  {build['started_at']}")
    console.print(f"  Finished: {build['finished_at'] or 'In progress'}")


@builds.command("logs")
@click.option("--id", "build_id", required=True, type=int, help="Build ID")
@click.pass_context
def build_logs(ctx, build_id):
    """View logs for a build."""
    resp = requests.get(f"{ctx.obj['api_url']}/api/builds/{build_id}/logs", timeout=10)
    if resp.status_code != 200:
        console.print(f"[red]Error:[/red] {_safe_error(resp)}")
        return

    data = resp.json()
    console.print(f"[bold]Logs for Build #{data['build_id']}[/bold]")
    console.print(data["logs"])


@builds.command("list")
@click.option("--app-id", default=None, type=int, help="Filter by application ID")
@click.pass_context
def list_builds(ctx, app_id):
    """List builds, optionally filtered by app."""
    url = f"{ctx.obj['api_url']}/api/builds"
    if app_id:
        url += f"?app_id={app_id}"

    resp = requests.get(url, timeout=10)
    if resp.status_code != 200:
        console.print(f"[red]Error:[/red] {_safe_error(resp)}")
        return
    data = resp.json()

    if not data:
        console.print("[yellow]No builds found.[/yellow]")
        return

    table = Table(title="Builds")
    table.add_column("ID", style="cyan")
    table.add_column("App", style="green")
    table.add_column("Branch")
    table.add_column("Status")
    table.add_column("Started")

    for build in data:
        status_color = {"pending": "yellow", "running": "blue", "success": "green", "failed": "red"}
        color = status_color.get(build["status"], "white")
        table.add_row(
            str(build["id"]),
            build["app_name"],
            build["branch"],
            f"[{color}]{build['status']}[/{color}]",
            build["started_at"][:19] if build["started_at"] else "N/A",
        )

    console.print(table)
