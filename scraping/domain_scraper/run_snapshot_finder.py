#!/usr/bin/env python3
"""
Simple runner script for the suburb snapshot finder
Provides easy-to-use commands for different scenarios

Usage:
    python run_snapshot_finder.py [command] [options]

Commands:
    all        - Find snapshots for all suburbs (all months)
    quarterly  - Find snapshots for March, June, September, December
    monthly    - Find snapshots for all months
    test       - Test with first 20 suburbs only
    resume     - Resume previous run
"""

import sys
import subprocess
from pathlib import Path


def run_command(cmd_args):
    """Run the snapshot finder with given arguments"""
    script_path = Path(__file__).parent / "find_suburb_snapshots_advanced.py"
    full_cmd = [sys.executable, str(script_path)] + cmd_args

    print(f"Running: {' '.join(full_cmd)}")
    print("-" * 50)

    try:
        result = subprocess.run(full_cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == "all":
        print("Finding snapshots for all suburbs (all months)...")
        run_command([])

    elif command == "quarterly":
        print("Finding snapshots for quarterly months (Mar, Jun, Sep, Dec)...")
        run_command(["--months", "3,6,9,12"])

    elif command == "monthly":
        print("Finding snapshots for all months...")
        run_command([])

    elif command == "test":
        print("Running in test mode (first 20 suburbs only)...")
        run_command(["--test"])

    elif command == "resume":
        print("Resuming previous run...")
        run_command(["--resume"])

    elif command == "help":
        print(__doc__)
        print("\nAdditional options:")
        print("  --start-year YEAR    Start year (default: 2022)")
        print("  --end-year YEAR      End year (default: 2025)")
        print("  --months 1,2,3       Specific months to target")
        print("\nExamples:")
        print("  python run_snapshot_finder.py test")
        print("  python run_snapshot_finder.py quarterly --start-year 2023")
        print("  python run_snapshot_finder.py all --months 1,7")

    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == "__main__":
    main()

