"""CLI commands for managing registered applications."""

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
def apps():
    """Manage applications."""


@apps.command("create")
@click.option("--name", required=True, help="Application name")
@click.option("--repo", required=True, help="Git repository URL")
@click.option("--language", default="python", help="Primary language (default: python)")
@click.pass_context
def create_app(ctx, name, repo, language):
    """Register a new application."""
    resp = requests.post(
        f"{ctx.obj['api_url']}/api/apps",
        json={"name": name, "repo_url": repo, "language": language},
        timeout=10,
    )
    if resp.status_code == 201:
        app = resp.json()
        console.print(f"[green]Created app '{app['name']}' (id={app['id']})[/green]")
    else:
        console.print(f"[red]Error:[/red] {_safe_error(resp)}")


@apps.command("list")
@click.pass_context
def list_apps(ctx):
    """List all registered applications."""
    resp = requests.get(f"{ctx.obj['api_url']}/api/apps", timeout=10)
    if resp.status_code != 200:
        console.print(f"[red]Error:[/red] {_safe_error(resp)}")
        return
    data = resp.json()

    if not data:
        console.print("[yellow]No applications registered yet.[/yellow]")
        return

    table = Table(title="Applications")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Language")
    table.add_column("Repo URL")
    table.add_column("Created")

    for app in data:
        table.add_row(
            str(app["id"]),
            app["name"],
            app["language"],
            app["repo_url"],
            app["created_at"][:19],
        )

    console.print(table)


@apps.command("delete")
@click.option("--id", "app_id", required=True, type=int, help="Application ID to delete")
@click.confirmation_option(prompt="Are you sure you want to delete this app?")
@click.pass_context
def delete_app(ctx, app_id):
    """Delete an application and all its builds."""
    resp = requests.delete(f"{ctx.obj['api_url']}/api/apps/{app_id}", timeout=10)
    if resp.status_code == 200:
        console.print(f"[green]{resp.json()['message']}[/green]")
    else:
        console.print(f"[red]Error:[/red] {_safe_error(resp)}")
