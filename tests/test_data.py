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


def test_apply_filters_sort_by(monkeypatch):
    """Test sorting logic in apply_filters."""
    import pandas as pd
    from cinescope.data import apply_filters
    
    mock_df = pd.DataFrame([
        {"movie_id": 1, "title": "B Movie", "vote_average": 7.0, "year": 2010, "runtime": 100, "genres_list": ["Action"]},
        {"movie_id": 2, "title": "A Movie", "vote_average": 9.0, "year": 2020, "runtime": 150, "genres_list": ["Action"]},
    ])
    monkeypatch.setattr("cinescope.data.get_movies", lambda: mock_df)
    
    # Sort by rating desc
    res_vote = apply_filters((), sort_by="vote_desc")
    assert res_vote.iloc[0]["title"] == "A Movie"
    
    # Sort by title asc
    res_title = apply_filters((), sort_by="title_asc")
    assert res_title.iloc[0]["title"] == "A Movie"
    assert res_title.iloc[1]["title"] == "B Movie"
