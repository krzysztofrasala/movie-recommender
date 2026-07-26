"""Tests for recommender module."""

from __future__ import annotations

from unittest.mock import patch
import pandas as pd

from cinescope.recommender import recommend, recommend_for_you


def test_recommend_empty_for_missing_movie():
    with patch("cinescope.data.get_movies") as mock_get_movies:
        mock_get_movies.return_value = pd.DataFrame({"title": ["Inception"], "movie_id": [1]})
        assert recommend("Nonexistent Movie") == []


def test_recommend_for_you_returns_empty_when_no_ratings(monkeypatch):
    import streamlit as st
    mock_session = {"rated_movies_info": {}, "user_ratings": {}}
    monkeypatch.setattr(st, "session_state", mock_session)
    assert recommend_for_you() == []


def test_recommend_for_group_empty_titles():
    from cinescope.recommender import recommend_for_group
    assert recommend_for_group([], []) == []

