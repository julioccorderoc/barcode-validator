"""CLI output formatting for ValidationResult."""

from barcode_validator.models import ValidationResult


def format_human(result: ValidationResult) -> str:
    """Format a ValidationResult as human-readable text for stderr."""
    lines = [
        f"File: {result.file}",
        f"Mode: {result.mode} | Passed: {'true' if result.passed else 'false'}",
    ]

    if result.barcodes:
        lines.append("Barcodes:")
        for bc in result.barcodes:
            parts = [f"format: {'OK' if bc.valid_format else 'FAIL'}"]
            if bc.valid_checkdigit is not None:
                parts.append(f"checkdigit: {'OK' if bc.valid_checkdigit else 'FAIL'}")
            if bc.matches_expected is not None:
                parts.append(f"match: {'OK' if bc.matches_expected else 'FAIL'}")
            detail = ", ".join(parts)
            lines.append(
                f"  [{bc.page}] {bc.value}  {bc.barcode_type.value}  ({detail})"
            )
    else:
        lines.append("Barcodes: (none)")

    lines.append(f"Summary: {result.summary}")
    return "\n".join(lines)


def format_json(result: ValidationResult) -> str:
    """Format a ValidationResult as JSON for stdout. Delegates to result.to_json()."""
    return result.to_json()


def format_error(file_path: str, error: Exception) -> str:
    """Format an error message for stderr."""
    return f"Error: {file_path}: {error}"
