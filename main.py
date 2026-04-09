"""
Multi-Agent Release Decision System
Entry point for running the complete workflow.

Usage:
    python -m app.main
    python app/main.py
"""

import sys
import os

# Ensure project root is on the path when running as script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import setup_logging, validate_config


def main() -> None:
    """Application entry point."""
    setup_logging()

    try:
        validate_config()
    except EnvironmentError as e:
        print(f"\n[ERROR] {e}")
        sys.exit(1)

    from app.orchestration.workflow import run_workflow

    try:
        run_workflow()
    except KeyboardInterrupt:
        print("\n[INFO] Workflow interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Workflow failed: {e}")
        raise


if __name__ == "__main__":
    main()
