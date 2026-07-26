"""Tests for the Movie Roulette and trailer functionality."""

from __future__ import annotations

from unittest.mock import patch
from cinescope import tmdb


def test_fetch_movie_trailer_returns_youtube_key():
    with patch("cinescope.tmdb._get") as mock_get:
        mock_get.return_value = {
            "results": [
                {"site": "YouTube", "type": "Trailer", "key": "abc123xyz"},
            ]
        }
        key = tmdb.fetch_movie_trailer(101)
        assert key == "abc123xyz"


def test_fetch_movie_trailer_returns_none_when_empty():
    with patch("cinescope.tmdb._get") as mock_get:
        mock_get.return_value = {"results": []}
        assert tmdb.fetch_movie_trailer(999) is None
