#!/usr/bin/env python3
"""Entry point for running the Job Hunter UI."""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the Streamlit application."""
    app_path = Path(__file__).parent / "src" / "ui" / "app.py"

    cmd = [
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]

    # Add any command line arguments
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    subprocess.run(cmd)


if __name__ == "__main__":
    main()
