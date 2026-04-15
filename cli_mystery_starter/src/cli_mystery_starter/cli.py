from __future__ import annotations

import argparse
from pathlib import Path

from .scaffold import create_project, load_config
from .validation import validate_project


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cli-mystery-starter",
        description="Scaffold and validate filesystem-based CLI mystery games.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Create a new mystery scaffold")
    init_parser.add_argument("target", help="Target directory for the new project")
    init_parser.add_argument(
        "--config",
        help="Optional JSON config file for project metadata",
    )

    validate_parser = subparsers.add_parser("validate", help="Validate a mystery project")
    validate_parser.add_argument("target", help="Target project directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        config = load_config(Path(args.config) if args.config else None)
        target = Path(args.target).resolve()
        written = create_project(target, config)
        print(f"Created scaffold at: {target}")
        print(f"Files written: {len(written)}")
        return 0

    if args.command == "validate":
        target = Path(args.target).resolve()
        errors = validate_project(target)
        if errors:
            print("Validation failed:")
            for error in errors:
                print(f"- {error}")
            return 1
        print("Validation passed.")
        return 0

    parser.error("Unknown command")
    return 2
