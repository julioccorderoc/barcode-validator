"""Tests for CLI argument parser."""

import pytest

from barcode_validator.cli_parser import build_parser, parse_args


class TestBuildParser:
    """Test that build_parser returns a configured ArgumentParser."""

    def test_returns_parser(self):
        parser = build_parser()
        assert parser.prog == "barcode-validator"


class TestParseArgsSingleFile:
    """Test parsing a single file argument."""

    def test_single_file(self):
        args = parse_args(["label.pdf"])
        assert args.files == ["label.pdf"]


class TestParseArgsMultipleFiles:
    """Test parsing multiple file arguments."""

    def test_multiple_files(self):
        args = parse_args(["a.pdf", "b.pdf"])
        assert args.files == ["a.pdf", "b.pdf"]


class TestParseArgsExpectedOnce:
    """Test --expected with a single value."""

    def test_expected_once(self):
        args = parse_args(["label.pdf", "--expected", "X001ABC123"])
        assert args.expected == ["X001ABC123"]


class TestParseArgsExpectedTwice:
    """Test --expected with two values."""

    def test_expected_twice(self):
        args = parse_args([
            "label.pdf",
            "--expected", "X001ABC123",
            "--expected", "012345678905",
        ])
        assert args.expected == ["X001ABC123", "012345678905"]


class TestParseArgsNoExpected:
    """Test that --expected defaults to None when absent."""

    def test_no_expected(self):
        args = parse_args(["label.pdf"])
        assert args.expected is None


class TestParseArgsJsonFlag:
    """Test the --json flag."""

    def test_json_present(self):
        args = parse_args(["label.pdf", "--json"])
        assert args.json is True

    def test_json_absent(self):
        args = parse_args(["label.pdf"])
        assert args.json is False


class TestParseArgsNoFiles:
    """Test that no files causes SystemExit."""

    def test_no_files_raises(self):
        with pytest.raises(SystemExit):
            parse_args([])


class TestParseArgsExpectedAndJson:
    """Test --expected and --json together."""

    def test_expected_and_json(self):
        args = parse_args([
            "label.pdf",
            "--expected", "X001ABC123",
            "--json",
        ])
        assert args.expected == ["X001ABC123"]
        assert args.json is True
        assert args.files == ["label.pdf"]


class TestParseArgsSpecialPaths:
    """Test file paths with spaces and parentheses."""

    def test_path_with_spaces_and_parens(self):
        args = parse_args(["(proof)(BL6)(540841).pdf"])
        assert args.files == ["(proof)(BL6)(540841).pdf"]

    def test_path_with_spaces(self):
        args = parse_args(["my label proof.pdf"])
        assert args.files == ["my label proof.pdf"]


class TestParseArgsOutput:
    """Test the --output / -o argument."""

    def test_output_long_form(self):
        args = parse_args(["label.pdf", "--output", "results.json"])
        assert args.output == "results.json"

    def test_output_short_form(self):
        args = parse_args(["label.pdf", "-o", "results.json"])
        assert args.output == "results.json"

    def test_output_defaults_to_none(self):
        args = parse_args(["label.pdf"])
        assert args.output is None

    def test_output_with_json_flag(self):
        args = parse_args(["label.pdf", "--output", "results.json", "--json"])
        assert args.output == "results.json"
        assert args.json is True


class TestParseArgsNoLookup:
    """Test the --no-lookup flag."""

    def test_no_lookup_flag_default(self):
        args = parse_args(["test.pdf"])
        assert args.no_lookup is False

    def test_no_lookup_flag_set(self):
        args = parse_args(["test.pdf", "--no-lookup"])
        assert args.no_lookup is True
