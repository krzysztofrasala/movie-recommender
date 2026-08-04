"""Tests for pure helpers in the TMDB client (no network calls)."""

from __future__ import annotations

from cinescope.tmdb import IMAGE_BASE_URL, PLACEHOLDER_POSTER, _movie_summary, poster_url


def test_poster_url_prepends_tmdb_image_base():
    assert poster_url("/abc.jpg") == f"{IMAGE_BASE_URL}/w500/abc.jpg"


def test_poster_url_custom_size():
    assert poster_url("/abc.jpg", size="w1280") == f"{IMAGE_BASE_URL}/w1280/abc.jpg"


def test_poster_url_none_returns_placeholder():
    """Missing posters would break <img> tags; use a graceful fallback."""
    assert poster_url(None) == PLACEHOLDER_POSTER
    assert poster_url("") == PLACEHOLDER_POSTER


def test_movie_summary_from_movie_payload():
    payload = {
        "id": 27205,
        "title": "Inception",
        "release_date": "2010-07-15",
        "vote_average": 8.36,
        "poster_path": "/inception.jpg",
        "overview": "A thief...",
    }
    summary = _movie_summary(payload)
    assert summary["id"] == 27205
    assert summary["title"] == "Inception"
    assert summary["year"] == "2010"
    assert summary["rating"] == 8.4  # rounded to one decimal for the UI
    assert summary["poster"].endswith("/inception.jpg")


def test_movie_summary_from_tv_payload():
    """TV endpoints use 'name' and 'first_air_date' instead of 'title'."""
    payload = {
        "id": 1396,
        "name": "Breaking Bad",
        "first_air_date": "2008-01-20",
        "vote_average": 8.9,
        "poster_path": "/bb.jpg",
        "overview": "...",
    }
    summary = _movie_summary(payload)
    assert summary["title"] == "Breaking Bad"
    assert summary["year"] == "2008"


def test_movie_summary_handles_missing_optional_fields():
    """Real TMDB responses often omit poster_path or dates for obscure titles."""
    summary = _movie_summary({"id": 1, "title": "X"})
    assert summary["year"] == ""
    assert summary["rating"] == 0
    assert summary["poster"] == PLACEHOLDER_POSTER
    assert summary["overview"] == ""


def test_smart_discover_with_language():
    from unittest.mock import patch
    from cinescope.tmdb import smart_discover

    with patch("cinescope.tmdb._get") as mock_get:
        mock_get.return_value = {"results": [{"id": 100, "title": "Znachor", "vote_average": 8.1, "poster_path": "/z.jpg"}]}
        results = smart_discover(genres=(), year_gte=None, year_lte=None, vote_gte=None, sort_by="popularity.desc", with_original_language="pl")
        assert len(results) == 1
        assert results[0]["title"] == "Znachor"
        mock_get.assert_called_once()
        call_params = mock_get.call_args[0][1]
        assert call_params["with_original_language"] == "pl"
        assert call_params["vote_count.gte"] == 10

