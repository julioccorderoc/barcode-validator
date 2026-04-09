"""Tests for barcode value comparator."""

from barcode_validator.comparator import match_expected


class TestMatchExpected:
    def test_match_all_found(self) -> None:
        matches, not_found = match_expected(["X004781QUF"], ["X004781QUF"])
        assert matches == {"X004781QUF": True}
        assert not_found == []

    def test_match_none_found(self) -> None:
        matches, not_found = match_expected(["X004781QUF"], ["DIFFERENT1"])
        assert matches == {"X004781QUF": False}
        assert not_found == ["DIFFERENT1"]

    def test_match_partial(self) -> None:
        matches, not_found = match_expected(["A", "B"], ["A", "C"])
        assert matches == {"A": True, "B": False}
        assert "C" in not_found

    def test_match_extra_decoded(self) -> None:
        matches, not_found = match_expected(["A", "B", "C"], ["A"])
        assert matches == {"A": True, "B": False, "C": False}
        assert not_found == []

    def test_match_empty_expected(self) -> None:
        matches, not_found = match_expected(["A"], [])
        assert matches == {"A": False}
        assert not_found == []

    def test_match_empty_decoded(self) -> None:
        matches, not_found = match_expected([], ["A"])
        assert matches == {}
        assert not_found == ["A"]

    def test_match_both_empty(self) -> None:
        matches, not_found = match_expected([], [])
        assert matches == {}
        assert not_found == []

    def test_match_case_sensitive(self) -> None:
        matches, not_found = match_expected(["x004781quf"], ["X004781QUF"])
        assert matches == {"x004781quf": False}
        assert not_found == ["X004781QUF"]

    def test_match_duplicates_decoded(self) -> None:
        matches, not_found = match_expected(["A", "A"], ["A"])
        assert matches["A"] is True
        assert not_found == []
