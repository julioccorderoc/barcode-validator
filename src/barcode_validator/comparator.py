"""Compare decoded barcode values against expected values."""


def match_expected(
    decoded_values: list[str],
    expected_values: list[str],
) -> tuple[dict[str, bool], list[str]]:
    """Compare decoded barcode values against expected values.

    Exact string comparison, case-sensitive.

    Returns:
        matches: dict mapping each decoded value to True/False
            (True if value is in expected)
        expected_not_found: list of expected values not found in decoded values
    """
    expected_set = set(expected_values)
    decoded_set = set(decoded_values)
    matches = {v: v in expected_set for v in decoded_values}
    expected_not_found = [e for e in expected_values if e not in decoded_set]
    return matches, expected_not_found
