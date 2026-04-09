"""CLI main orchestrator for barcode-validator."""

import sys

from barcode_validator import validate_label
from barcode_validator.cli_parser import parse_args
from barcode_validator.cli_format import format_human, format_json, format_error


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns exit code (0=pass, 1=fail, 2=error)."""
    args = parse_args(argv)
    exit_code = 0
    for file_path in args.files:
        try:
            result = validate_label(file_path, expected_barcodes=args.expected)
            if args.json:
                print(format_json(result))
            else:
                print(format_human(result), file=sys.stderr)
            if not result.passed:
                exit_code = max(exit_code, 1)
        except (FileNotFoundError, ValueError) as exc:
            print(format_error(file_path, exc), file=sys.stderr)
            exit_code = max(exit_code, 2)
        except Exception as exc:
            print(format_error(file_path, exc), file=sys.stderr)
            exit_code = max(exit_code, 2)
    return exit_code
