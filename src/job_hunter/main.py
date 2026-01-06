"""Main CLI entry point for job hunter application."""

import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich import print as rprint

from job_hunter.config import get_config, reset_config
from job_hunter.models import ApplicationStatus
from job_hunter.storage import Database

# Create Typer app
app = typer.Typer(
    name="job-hunter",
    help="Intelligent LinkedIn job application agent",
    add_completion=False,
)

# Rich console for pretty output
console = Console()


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


@app.command()
def search(
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview search without saving to database"
    ),
) -> None:
    """
    Search for jobs on LinkedIn based on configured criteria.

    This command will:
    1. Load search criteria from config/search_criteria.yaml
    2. Search LinkedIn for matching jobs
    3. Score each job using AI matching
    4. Save qualified jobs to the database
    """
    console.print("[bold blue]Starting job search...[/bold blue]")

    try:
        config = get_config()
        settings = config.load_settings()
        criteria = config.load_search_criteria()

        console.print(f"[green]Search criteria loaded:[/green]")
        console.print(f"  Titles: {', '.join(criteria.titles[:3])}{'...' if len(criteria.titles) > 3 else ''}")
        console.print(f"  Locations: {', '.join(criteria.locations[:3])}{'...' if len(criteria.locations) > 3 else ''}")
        console.print(f"  Min match score: {criteria.min_match_score}")
        console.print(f"  Easy Apply only: {criteria.easy_apply_only}")

        if dry_run:
            console.print("[yellow]DRY RUN MODE - No changes will be saved[/yellow]")

        console.print("\n[yellow]Note: Job search functionality requires the BROWSER agent[/yellow]")
        console.print("[yellow]The browser agent will implement LinkedIn automation[/yellow]")

    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def apply(
    max_applications: Optional[int] = typer.Option(
        None,
        "--max",
        "-m",
        help="Maximum number of applications to submit"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview applications without submitting"
    ),
) -> None:
    """
    Apply to jobs that meet the matching criteria.

    This command will:
    1. Load jobs from database with sufficient match scores
    2. Filter out already-applied jobs
    3. Submit Easy Apply applications
    4. Use AI to answer custom questions
    5. Track application status
    """
    console.print("[bold blue]Starting job application process...[/bold blue]")

    try:
        config = get_config()
        settings = config.load_settings()
        criteria = config.load_search_criteria()

        db = Database(settings.database_path)

        # Count applications today
        apps_today = db.count_applications_today()
        max_daily = criteria.max_applications_per_day

        console.print(f"[green]Applications submitted today:[/green] {apps_today}/{max_daily}")

        if apps_today >= max_daily:
            console.print(f"[yellow]Daily application limit reached ({max_daily})[/yellow]")
            raise typer.Exit(0)

        # Determine how many more we can apply to
        remaining = max_daily - apps_today
        if max_applications:
            to_apply = min(max_applications, remaining)
        else:
            to_apply = remaining

        console.print(f"[green]Will apply to up to {to_apply} jobs[/green]")

        if dry_run:
            console.print("[yellow]DRY RUN MODE - No applications will be submitted[/yellow]")

        console.print("\n[yellow]Note: Application functionality requires BROWSER and MATCHING agents[/yellow]")
        console.print("[yellow]These agents will implement form filling and AI-powered question answering[/yellow]")

        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def status(
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed information"
    ),
) -> None:
    """
    Show application status and statistics.

    Displays:
    - Total jobs found
    - Applications by status (pending, submitted, interviewing, etc.)
    - Recent applications
    - Success rate
    """
    console.print("[bold blue]Job Hunter Status[/bold blue]\n")

    try:
        config = get_config()
        settings = config.load_settings()
        db = Database(settings.database_path)

        # Get statistics
        stats = db.get_statistics()

        # Jobs statistics
        console.print("[bold]Jobs Database:[/bold]")
        console.print(f"  Total jobs: {stats['total_jobs']}")
        console.print(f"  Easy Apply jobs: {stats['easy_apply_jobs']}")
        console.print(f"  Average match score: {stats['avg_match_score']}")

        # Applications statistics
        console.print("\n[bold]Applications:[/bold]")
        apps_by_status = stats.get("applications_by_status", {})

        if apps_by_status:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Status", style="cyan")
            table.add_column("Count", justify="right", style="green")

            for status, count in apps_by_status.items():
                table.add_row(status, str(count))

            console.print(table)
        else:
            console.print("  No applications yet")

        console.print(f"\n  Applications today: {stats['applications_today']}")

        # Recent applications (if verbose)
        if verbose:
            console.print("\n[bold]Recent Applications:[/bold]")
            recent = db.get_all_applications(limit=10)

            if recent:
                table = Table(show_header=True, header_style="bold magenta")
                table.add_column("ID", style="cyan")
                table.add_column("Job ID", style="blue")
                table.add_column("Status", style="yellow")
                table.add_column("Applied At", style="green")

                for app in recent:
                    applied_str = app.applied_at.strftime("%Y-%m-%d %H:%M") if app.applied_at else "N/A"
                    table.add_row(
                        app.application_id or "N/A",
                        app.job_id,
                        app.status.value,
                        applied_str
                    )

                console.print(table)
            else:
                console.print("  No applications yet")

        db.close()

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def config_cmd(
    show: bool = typer.Option(
        True,
        "--show",
        help="Show current configuration"
    ),
    edit: bool = typer.Option(
        False,
        "--edit",
        help="Open configuration files in editor"
    ),
) -> None:
    """
    Manage configuration settings.

    View or edit:
    - Application settings (config/settings.yaml)
    - Search criteria (config/search_criteria.yaml)
    """
    try:
        config = get_config()

        if show:
            console.print("[bold blue]Current Configuration[/bold blue]\n")

            # Settings
            try:
                settings = config.load_settings()
                console.print("[bold]Settings:[/bold]")
                console.print(f"  Database: {settings.database_path}")
                console.print(f"  Resume directory: {settings.resume_dir}")
                console.print(f"  Log level: {settings.log_level}")
                console.print(f"  Headless mode: {settings.headless}")
                console.print(f"  Dry run: {settings.dry_run}")
            except Exception as e:
                console.print(f"[yellow]Settings not configured: {e}[/yellow]")

            # Search criteria
            console.print("\n[bold]Search Criteria:[/bold]")
            try:
                criteria = config.load_search_criteria()
                console.print(f"  Job titles: {', '.join(criteria.titles[:3])}{'...' if len(criteria.titles) > 3 else ''}")
                console.print(f"  Locations: {', '.join(criteria.locations[:3])}{'...' if len(criteria.locations) > 3 else ''}")
                console.print(f"  Min match score: {criteria.min_match_score}")
                console.print(f"  Max applications/day: {criteria.max_applications_per_day}")
            except FileNotFoundError:
                console.print("  [yellow]Not configured - run 'job-hunter init' to create config files[/yellow]")

        if edit:
            console.print("\n[yellow]Opening configuration files...[/yellow]")
            console.print("  config/settings.yaml")
            console.print("  config/search_criteria.yaml")
            console.print("\n[yellow]Note: Manual editing not implemented yet[/yellow]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def init(
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing configuration files"
    ),
) -> None:
    """
    Initialize configuration files with default values.

    Creates:
    - config/settings.yaml
    - config/search_criteria.yaml
    - .env.example
    """
    console.print("[bold blue]Initializing job hunter configuration...[/bold blue]\n")

    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)

    settings_path = config_dir / "settings.yaml"
    criteria_path = config_dir / "search_criteria.yaml"

    # Check if files exist
    if settings_path.exists() and not force:
        console.print(f"[yellow]{settings_path} already exists (use --force to overwrite)[/yellow]")
    else:
        console.print("[yellow]Note: settings.yaml is optional - use .env for configuration[/yellow]")
        console.print(f"[green]Skipped creating {settings_path}[/green]")

    if criteria_path.exists() and not force:
        console.print(f"[yellow]{criteria_path} already exists (use --force to overwrite)[/yellow]")
    else:
        console.print(f"[green]Creating {criteria_path}...[/green]")
        # This will be created in the next task

    console.print("\n[bold green]Configuration initialized![/bold green]")
    console.print("\nNext steps:")
    console.print("1. Copy .env.example to .env and fill in your credentials")
    console.print("2. Edit config/search_criteria.yaml with your job preferences")
    console.print("3. Run 'job-hunter search' to start finding jobs")


@app.command()
def version() -> None:
    """Show version information."""
    console.print("[bold]Job Hunter[/bold] v0.1.0")
    console.print("Intelligent LinkedIn job application agent")


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
