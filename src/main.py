"""Job Hunter CLI - LinkedIn Job Application Agent."""

import shutil
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.config import (
    CONFIG_DIR,
    RESUMES_DIR,
    Settings,
    load_settings,
)
from src.resume.parser import ResumeParser
from src.resume.profile import UserProfile

app = typer.Typer(
    name="job-hunter",
    help="LinkedIn Job Application Agent - Automate your job search",
    add_completion=False,
)
console = Console()


def get_settings() -> Settings:
    """Load settings with error handling."""
    try:
        return load_settings()
    except Exception as e:
        console.print(f"[red]Error loading settings: {e}[/red]")
        raise typer.Exit(1)


# ============================================================================
# Resume Commands
# ============================================================================

resume_app = typer.Typer(help="Manage your resume")
app.add_typer(resume_app, name="resume")


@resume_app.command("upload")
def resume_upload(
    file_path: Path = typer.Argument(
        ...,
        help="Path to your resume file (PDF or JSON)",
        exists=True,
        readable=True,
    ),
    parse: bool = typer.Option(
        True, "--parse/--no-parse", help="Parse the resume after uploading"
    ),
) -> None:
    """Upload a resume file (PDF or JSON) for job matching.

    The resume will be copied to the data/resumes directory and optionally
    parsed to extract your profile information.

    Examples:
        job-hunter resume upload ~/Documents/my_resume.pdf
        job-hunter resume upload profile.json --no-parse
    """
    # Determine file type
    suffix = file_path.suffix.lower()
    if suffix not in [".pdf", ".json"]:
        console.print(
            f"[red]Error: Unsupported file type '{suffix}'. "
            "Please use PDF or JSON format.[/red]"
        )
        raise typer.Exit(1)

    # Copy to resumes directory
    dest_path = RESUMES_DIR / file_path.name
    try:
        shutil.copy2(file_path, dest_path)
        console.print(f"[green]✓ Resume copied to:[/green] {dest_path}")
    except Exception as e:
        console.print(f"[red]Error copying file: {e}[/red]")
        raise typer.Exit(1)

    # Parse if requested
    if parse:
        console.print("\n[bold]Parsing resume...[/bold]")
        try:
            parser = ResumeParser()
            profile = parser.parse(str(dest_path))
            _display_profile_summary(profile)

            # Update settings with resume path
            console.print(
                f"\n[dim]To use this resume, add to config/settings.yaml:[/dim]"
            )
            console.print(f"[cyan]resume_path: {dest_path}[/cyan]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not parse resume: {e}[/yellow]")
            console.print("[dim]You can still use the file for manual reference.[/dim]")


@resume_app.command("parse")
def resume_parse(
    file_path: Optional[Path] = typer.Argument(
        None,
        help="Path to resume file (uses configured resume if not provided)",
        exists=True,
        readable=True,
    ),
) -> None:
    """Parse a resume and display extracted information.

    Examples:
        job-hunter resume parse
        job-hunter resume parse ~/Documents/resume.pdf
    """
    # Determine which file to parse
    if file_path is None:
        settings = get_settings()
        if settings.resume_path:
            file_path = Path(settings.resume_path)
        else:
            # Look for any resume in the resumes directory
            resumes = list(RESUMES_DIR.glob("*.pdf")) + list(RESUMES_DIR.glob("*.json"))
            if resumes:
                file_path = resumes[0]
                console.print(f"[dim]Using: {file_path}[/dim]")
            else:
                console.print(
                    "[red]No resume found. Please upload one first:[/red]\n"
                    "  job-hunter resume upload <path-to-resume>"
                )
                raise typer.Exit(1)

    try:
        parser = ResumeParser()
        profile = parser.parse(str(file_path))
        _display_profile_summary(profile)
    except Exception as e:
        console.print(f"[red]Error parsing resume: {e}[/red]")
        raise typer.Exit(1)


@resume_app.command("list")
def resume_list() -> None:
    """List all uploaded resumes."""
    resumes = list(RESUMES_DIR.glob("*.pdf")) + list(RESUMES_DIR.glob("*.json"))

    if not resumes:
        console.print("[yellow]No resumes found.[/yellow]")
        console.print("Upload one with: [cyan]job-hunter resume upload <path>[/cyan]")
        return

    table = Table(title="Uploaded Resumes")
    table.add_column("File", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Size", justify="right")

    for resume in sorted(resumes):
        file_type = "PDF" if resume.suffix == ".pdf" else "JSON"
        size = f"{resume.stat().st_size / 1024:.1f} KB"
        table.add_row(resume.name, file_type, size)

    console.print(table)


def _display_profile_summary(profile: UserProfile) -> None:
    """Display a summary of the parsed profile."""
    # Contact info
    contact_info = f"[bold]{profile.contact.name}[/bold]\n"
    contact_info += f"Email: {profile.contact.email}\n"
    if profile.contact.phone:
        contact_info += f"Phone: {profile.contact.phone}\n"
    if profile.contact.location:
        contact_info += f"Location: {profile.contact.location}\n"
    if profile.contact.linkedin_url:
        contact_info += f"LinkedIn: {profile.contact.linkedin_url}"

    console.print(Panel(contact_info, title="Contact Information", border_style="blue"))

    # Summary
    if profile.summary:
        console.print(Panel(profile.summary, title="Summary", border_style="green"))

    # Experience
    if profile.work_experience:
        exp_table = Table(title="Work Experience", show_header=True)
        exp_table.add_column("Title", style="cyan")
        exp_table.add_column("Company", style="green")
        exp_table.add_column("Duration")

        for exp in profile.work_experience[:5]:  # Show top 5
            exp_table.add_row(exp.title, exp.company, exp.duration_text or "")

        console.print(exp_table)

    # Skills
    if profile.skills:
        skills_text = ", ".join(profile.skills[:15])  # Show top 15
        if len(profile.skills) > 15:
            skills_text += f" [dim](+{len(profile.skills) - 15} more)[/dim]"
        console.print(Panel(skills_text, title="Skills", border_style="yellow"))

    # Stats
    stats = (
        f"Work Experience: {len(profile.work_experience)} positions | "
        f"Skills: {len(profile.skills)} | "
        f"Education: {len(profile.education)}"
    )
    console.print(f"\n[dim]{stats}[/dim]")


# ============================================================================
# Config Commands
# ============================================================================


@app.command("config")
def show_config() -> None:
    """Display current configuration settings."""
    settings = get_settings()

    # Main settings
    table = Table(title="Settings")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Resume Path", settings.resume_path or "[dim]Not set[/dim]")
    table.add_row("Database Path", settings.database_path)
    table.add_row("Headless Browser", str(settings.headless_browser))
    table.add_row("Dry Run", str(settings.dry_run))
    table.add_row("Verbose", str(settings.verbose))

    # API key status (don't show actual values)
    api_status = "[green]Set[/green]" if settings.anthropic_api_key else "[red]Not set[/red]"
    table.add_row("Anthropic API Key", api_status)

    linkedin_status = "[green]Set[/green]" if settings.linkedin_email else "[red]Not set[/red]"
    table.add_row("LinkedIn Credentials", linkedin_status)

    console.print(table)

    # Search criteria
    criteria_table = Table(title="Search Criteria")
    criteria_table.add_column("Setting", style="cyan")
    criteria_table.add_column("Value", style="green")

    criteria = settings.search_criteria
    criteria_table.add_row("Target Roles", ", ".join(criteria.target_roles[:3]) + "...")
    criteria_table.add_row("Locations", ", ".join(criteria.locations))
    criteria_table.add_row("Excluded Locations", ", ".join(criteria.excluded_locations))
    criteria_table.add_row("Min Match Score", str(criteria.min_match_score))
    criteria_table.add_row("Easy Apply Only", str(criteria.easy_apply_only))

    console.print(criteria_table)

    # Rate limits
    rate_table = Table(title="Rate Limits")
    rate_table.add_column("Setting", style="cyan")
    rate_table.add_column("Value", style="green")

    limits = settings.rate_limits
    rate_table.add_row("Delay Range", f"{limits.min_delay_seconds}-{limits.max_delay_seconds}s")
    rate_table.add_row("Max Applications/Day", str(limits.max_applications_per_day))
    rate_table.add_row("Max Searches/Hour", str(limits.max_searches_per_hour))

    console.print(rate_table)

    console.print(f"\n[dim]Config files: {CONFIG_DIR}[/dim]")


# ============================================================================
# Status Command
# ============================================================================


@app.command("status")
def show_status() -> None:
    """Show current application status and statistics."""
    settings = get_settings()

    # Check resume
    resume_status = "[green]✓ Configured[/green]" if settings.resume_path else "[yellow]Not configured[/yellow]"
    resumes_count = len(list(RESUMES_DIR.glob("*.pdf"))) + len(list(RESUMES_DIR.glob("*.json")))

    # Check credentials
    api_status = "[green]✓ Set[/green]" if settings.anthropic_api_key else "[red]✗ Missing[/red]"
    linkedin_status = "[green]✓ Set[/green]" if settings.linkedin_email else "[red]✗ Missing[/red]"

    console.print(Panel.fit(
        f"[bold]Job Hunter Status[/bold]\n\n"
        f"Resume: {resume_status} ({resumes_count} files in data/resumes/)\n"
        f"Anthropic API Key: {api_status}\n"
        f"LinkedIn Credentials: {linkedin_status}\n\n"
        f"[dim]Database: {settings.database_path}[/dim]",
        border_style="blue",
    ))

    # Show next steps if not ready
    if not settings.resume_path or not settings.anthropic_api_key or not settings.linkedin_email:
        console.print("\n[bold yellow]Setup Required:[/bold yellow]")
        if not settings.resume_path and resumes_count == 0:
            console.print("  1. Upload your resume: [cyan]job-hunter resume upload <path>[/cyan]")
        if not settings.anthropic_api_key:
            console.print("  2. Set ANTHROPIC_API_KEY environment variable")
        if not settings.linkedin_email:
            console.print("  3. Set LINKEDIN_EMAIL and LINKEDIN_PASSWORD environment variables")


# ============================================================================
# Search & Apply Commands (Placeholders)
# ============================================================================


@app.command("search")
def search_jobs(
    query: Optional[str] = typer.Argument(None, help="Custom search query"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum jobs to find"),
) -> None:
    """Search for jobs matching your criteria.

    Uses the search criteria from config/search_criteria.yaml
    """
    console.print("[yellow]Search functionality not yet implemented.[/yellow]")
    console.print("[dim]This will search LinkedIn for jobs matching your criteria.[/dim]")

    settings = get_settings()
    console.print(f"\n[dim]Would search for: {', '.join(settings.search_criteria.target_roles[:3])}...[/dim]")
    console.print(f"[dim]In locations: {', '.join(settings.search_criteria.locations)}[/dim]")


@app.command("apply")
def apply_jobs(
    job_id: Optional[str] = typer.Argument(None, help="Specific job ID to apply to"),
    auto: bool = typer.Option(False, "--auto", "-a", help="Auto-apply to matching jobs"),
    dry_run: bool = typer.Option(False, "--dry-run", "-d", help="Simulate without applying"),
) -> None:
    """Apply to jobs (Easy Apply only).

    Can apply to a specific job or auto-apply to all matching jobs.
    """
    console.print("[yellow]Apply functionality not yet implemented.[/yellow]")
    console.print("[dim]This will handle LinkedIn Easy Apply submissions.[/dim]")


# ============================================================================
# Main Entry Point
# ============================================================================


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Show version"),
) -> None:
    """Job Hunter - LinkedIn Job Application Agent.

    Automate your job search and application process on LinkedIn.

    Quick Start:
        1. Upload your resume: job-hunter resume upload <path>
        2. Set environment variables (see README)
        3. Configure search: edit config/search_criteria.yaml
        4. Search for jobs: job-hunter search
        5. Apply to jobs: job-hunter apply --auto
    """
    if version:
        console.print("Job Hunter v0.1.0")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


if __name__ == "__main__":
    app()
