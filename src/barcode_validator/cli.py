"""CLI main orchestrator for barcode-validator."""

import sys
from pathlib import Path

from barcode_validator import validate_label
from barcode_validator.cli_parser import parse_args
from barcode_validator.cli_format import format_human, format_json, format_json_array, format_error
from barcode_validator.lookup import create_lookup_service


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns exit code (0=pass, 1=fail, 2=error)."""
    args = parse_args(argv)
    exit_code = 0

    if args.output:
        args.json = True
        output_path = Path(args.output)
        if not output_path.parent.exists():
            print(f"Error: output directory does not exist: {output_path.parent}", file=sys.stderr)
            return 2

    lookup_service = None if args.no_lookup else create_lookup_service()

    results = []
    for file_path in args.files:
        try:
            result = validate_label(file_path, expected_barcodes=args.expected, lookup_service=lookup_service)
            if args.output:
                results.append(result)
            elif args.json:
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

    if args.output:
        try:
            output_path.write_text(format_json_array(results))
        except OSError as exc:
            print(f"Error: cannot write output file: {exc}", file=sys.stderr)
            exit_code = max(exit_code, 2)

    return exit_code
