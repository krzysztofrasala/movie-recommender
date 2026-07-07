"""Tests for parsing helpers in the data module (pure functions, no I/O)."""

from __future__ import annotations

from cinescope.data import parse_genres


def test_parse_genres_typical_input():
    """The stringified list format TMDB stores in movies.csv."""
    raw = "[{'id': 28, 'name': 'Action'}, {'id': 12, 'name': 'Adventure'}]"
    assert parse_genres(raw) == ["Action", "Adventure"]


def test_parse_genres_empty_list():
    assert parse_genres("[]") == []


def test_parse_genres_handles_malformed_input():
    """Never raise — the CSV is untrusted and rare rows can be junk."""
    assert parse_genres("not-a-list") == []
    assert parse_genres("") == []
    assert parse_genres(None) == []


def test_parse_genres_missing_name_key():
    """A row without the expected 'name' key must degrade to []."""
    assert parse_genres("[{'id': 28}]") == []
