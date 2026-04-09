"""Tests for CLI main orchestrator (cli.py).

All dependencies are mocked since Streams A and B are built in parallel.
"""

import argparse

import pytest

from barcode_validator.models import ValidationResult


# --- Helpers ---

def _make_ns(files: list[str], expected: list[str] | None = None, json: bool = False) -> argparse.Namespace:
    return argparse.Namespace(files=files, expected=expected, json=json)


def _make_result(file: str, passed: bool) -> ValidationResult:
    return ValidationResult(
        file=file,
        passed=passed,
        mode="decode",
        barcodes=[],
        expected_not_found=[],
        summary="OK" if passed else "FAIL",
    )


def _patch_cli(monkeypatch, ns, results=None, exc_map=None):
    """Patch all cli dependencies.

    results: dict mapping file path -> ValidationResult
    exc_map: dict mapping file path -> exception instance to raise
    """
    from barcode_validator import cli  # noqa: ensure module is imported

    monkeypatch.setattr("barcode_validator.cli.parse_args", lambda argv: ns)

    results = results or {}
    exc_map = exc_map or {}

    def fake_validate(f, expected_barcodes=None):
        if f in exc_map:
            raise exc_map[f]
        return results[f]

    monkeypatch.setattr("barcode_validator.cli.validate_label", fake_validate)
    monkeypatch.setattr("barcode_validator.cli.format_human", lambda r: f"human: {r.summary}")
    monkeypatch.setattr("barcode_validator.cli.format_json", lambda r: f'{{"file": "{r.file}"}}')
    monkeypatch.setattr("barcode_validator.cli.format_error", lambda f, e: f"Error: {f}: {e}")


# --- Exit code tests ---


class TestExitCodes:
    def test_single_file_pass(self, monkeypatch):
        from barcode_validator.cli import main

        ns = _make_ns(files=["test.pdf"])
        _patch_cli(monkeypatch, ns, results={"test.pdf": _make_result("test.pdf", True)})
        assert main() == 0

    def test_single_file_fail(self, monkeypatch):
        from barcode_validator.cli import main

        ns = _make_ns(files=["test.pdf"])
        _patch_cli(monkeypatch, ns, results={"test.pdf": _make_result("test.pdf", False)})
        assert main() == 1

    def test_file_not_found_returns_2(self, monkeypatch):
        from barcode_validator.cli import main

        ns = _make_ns(files=["missing.pdf"])
        _patch_cli(monkeypatch, ns, exc_map={"missing.pdf": FileNotFoundError("not found")})
        assert main() == 2

    def test_value_error_returns_2(self, monkeypatch):
        from barcode_validator.cli import main

        ns = _make_ns(files=["bad.eps"])
        _patch_cli(monkeypatch, ns, exc_map={"bad.eps": ValueError("unsupported format")})
        assert main() == 2

    def test_batch_both_pass(self, monkeypatch):
        from barcode_validator.cli import main

        ns = _make_ns(files=["a.pdf", "b.pdf"])
        _patch_cli(monkeypatch, ns, results={
            "a.pdf": _make_result("a.pdf", True),
            "b.pdf": _make_result("b.pdf", True),
        })
        assert main() == 0

    def test_batch_one_pass_one_fail(self, monkeypatch):
        from barcode_validator.cli import main

        ns = _make_ns(files=["a.pdf", "b.pdf"])
        _patch_cli(monkeypatch, ns, results={
            "a.pdf": _make_result("a.pdf", True),
            "b.pdf": _make_result("b.pdf", False),
        })
        assert main() == 1

    def test_batch_one_pass_one_error(self, monkeypatch):
        from barcode_validator.cli import main

        ns = _make_ns(files=["a.pdf", "b.pdf"])
        _patch_cli(monkeypatch, ns, results={
            "a.pdf": _make_result("a.pdf", True),
        }, exc_map={
            "b.pdf": FileNotFoundError("not found"),
        })
        assert main() == 2

    def test_batch_one_fail_one_error(self, monkeypatch):
        from barcode_validator.cli import main

        ns = _make_ns(files=["a.pdf", "b.pdf"])
        _patch_cli(monkeypatch, ns, results={
            "a.pdf": _make_result("a.pdf", False),
        }, exc_map={
            "b.pdf": FileNotFoundError("not found"),
        })
        assert main() == 2

    def test_unexpected_exception_returns_2(self, monkeypatch):
        from barcode_validator.cli import main

        ns = _make_ns(files=["corrupt.pdf"])
        _patch_cli(monkeypatch, ns, exc_map={"corrupt.pdf": RuntimeError("segfault")})
        assert main() == 2


# --- Output routing tests ---


class TestOutputRouting:
    def test_default_mode_human_to_stderr(self, monkeypatch, capsys):
        from barcode_validator.cli import main

        ns = _make_ns(files=["test.pdf"], json=False)
        _patch_cli(monkeypatch, ns, results={"test.pdf": _make_result("test.pdf", True)})
        main()
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "human: OK" in captured.err

    def test_json_mode_to_stdout(self, monkeypatch, capsys):
        from barcode_validator.cli import main

        ns = _make_ns(files=["test.pdf"], json=True)
        _patch_cli(monkeypatch, ns, results={"test.pdf": _make_result("test.pdf", True)})
        main()
        captured = capsys.readouterr()
        assert '{"file": "test.pdf"}' in captured.out
        assert captured.err == ""

    def test_error_goes_to_stderr(self, monkeypatch, capsys):
        from barcode_validator.cli import main

        ns = _make_ns(files=["missing.pdf"])
        _patch_cli(monkeypatch, ns, exc_map={"missing.pdf": FileNotFoundError("not found")})
        main()
        captured = capsys.readouterr()
        assert captured.out == ""
        assert "Error: missing.pdf" in captured.err


# --- Batch behavior tests ---


class TestBatchBehavior:
    def test_each_file_produces_output(self, monkeypatch, capsys):
        from barcode_validator.cli import main

        ns = _make_ns(files=["a.pdf", "b.pdf"], json=True)
        _patch_cli(monkeypatch, ns, results={
            "a.pdf": _make_result("a.pdf", True),
            "b.pdf": _make_result("b.pdf", True),
        })
        main()
        captured = capsys.readouterr()
        assert '{"file": "a.pdf"}' in captured.out
        assert '{"file": "b.pdf"}' in captured.out

    def test_processing_continues_after_error(self, monkeypatch, capsys):
        from barcode_validator.cli import main

        ns = _make_ns(files=["bad.pdf", "good.pdf"], json=True)
        _patch_cli(monkeypatch, ns, results={
            "good.pdf": _make_result("good.pdf", True),
        }, exc_map={
            "bad.pdf": FileNotFoundError("not found"),
        })
        main()
        captured = capsys.readouterr()
        # good.pdf should still produce output despite bad.pdf erroring
        assert '{"file": "good.pdf"}' in captured.out
        assert "Error: bad.pdf" in captured.err
