"""CLI argument parser for barcode-validator."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="barcode-validator",
        description="Validate barcodes on label proofs",
    )
    parser.add_argument(
        "files",
        nargs="+",
        help="one or more file paths to validate",
    )
    parser.add_argument(
        "--expected",
        action="append",
        default=None,
        help="expected barcode value (repeatable)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="output JSON to stdout",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="write JSON results to file (implies --json)",
    )
    parser.add_argument(
        "--no-lookup",
        action="store_true",
        default=False,
        help="disable public barcode lookup (offline mode)",
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments. Returns namespace with: files, expected, json, output, no_lookup."""
    parser = build_parser()
    return parser.parse_args(argv)
