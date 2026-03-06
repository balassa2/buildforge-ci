"""BuildForge CLI -- command-line interface for the CI/CD platform."""

import os

import click

from buildforge_cli.commands.apps import apps
from buildforge_cli.commands.builds import builds

API_URL = os.environ.get("BUILDFORGE_API_URL", "http://localhost:5000")


@click.group()
@click.pass_context
def cli(ctx):
    """BuildForge CI/CD Platform CLI."""
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = API_URL


cli.add_command(apps, "app")
cli.add_command(builds, "build")


if __name__ == "__main__":
    cli()
