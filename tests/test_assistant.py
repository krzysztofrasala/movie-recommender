"""Tests for the AI assistant tools module."""

from __future__ import annotations

from unittest.mock import patch
from cinescope.ui.tabs.assistant import search_movies_tool, get_similar_movies_tool, get_trending_movies_tool


def test_search_movies_tool_delegates_to_tmdb():
    with patch("cinescope.tmdb.search_movies") as mock_search:
        mock_search.return_value = [{"id": 1, "title": "Inception"}]
        res = search_movies_tool("Inception")
        assert res == [{"id": 1, "title": "Inception"}]
        mock_search.assert_called_once_with("Inception")


def test_get_similar_movies_tool_delegates_to_recommender():
    with patch("cinescope.recommender.more_like_this") as mock_rec:
        mock_rec.return_value = [{"id": 2, "title": "Interstellar"}]
        res = get_similar_movies_tool("Inception")
        assert res == [{"id": 2, "title": "Interstellar"}]
        mock_rec.assert_called_once_with(0, "Inception")


def test_get_trending_movies_tool_delegates_to_tmdb():
    with patch("cinescope.tmdb.fetch_trending") as mock_trending:
        mock_trending.return_value = [{"id": 3, "title": "Avatar"}]
        res = get_trending_movies_tool()
        assert res == [{"id": 3, "title": "Avatar"}]
        mock_trending.assert_called_once()


def test_search_tv_tool_delegates_to_tmdb():
    from cinescope.ui.tabs.assistant import search_tv_tool
    with patch("cinescope.tmdb.search_tv") as mock_tv:
        mock_tv.return_value = [{"id": 4, "title": "Fauda"}]
        res = search_tv_tool("Fauda")
        assert res == [{"id": 4, "title": "Fauda"}]
        mock_tv.assert_called_once_with("Fauda")


def test_smart_search_fallback_detects_tv_shows_and_translates_keywords():
    from cinescope.ui.tabs.assistant import _smart_search_fallback

    with patch("cinescope.tmdb.search_tv") as mock_tv:
        mock_tv.return_value = [{"id": 10, "title": "Wildest Middle East"}]
        msg, results = _smart_search_fallback("znajdź mi serial o bliskim wschodzie")
        assert "TMDB" in msg
        assert len(results) == 1
        assert results[0]["title"] == "Wildest Middle East"
