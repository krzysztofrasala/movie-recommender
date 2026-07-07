"""Tests for small HTML/URL helpers used by every card and dialog."""

from __future__ import annotations

import pytest

from cinescope.ui.html import (
    format_runtime,
    genre_chips_html,
    justwatch_url,
    poster_html,
    provider_logos_html,
    rating_color,
)


@pytest.mark.parametrize("rating,expected", [
    (9.5, "#2ECC71"), (7.5, "#2ECC71"),  # green: >= 7.5
    (7.4, "#F39C12"), (6.0, "#F39C12"),  # orange: [6.0, 7.5)
    (5.9, "#E74C3C"), (0.0, "#E74C3C"),  # red:   < 6.0
])
def test_rating_color_thresholds(rating: float, expected: str):
    """Traffic-light thresholds must be inclusive on the lower bound."""
    assert rating_color(rating) == expected


@pytest.mark.parametrize("minutes,expected", [
    (0, ""),      # zero minutes = no runtime known → no label
    (None, ""),   # missing data is common in TMDB
    (45, "45m"),
    (60, "1h 0m"),
    (135, "2h 15m"),
])
def test_format_runtime(minutes, expected: str):
    assert format_runtime(minutes) == expected


def test_justwatch_url_percent_encodes_title():
    """Titles with spaces or specials must survive as a query string."""
    url = justwatch_url("The Lord of the Rings & Hobbit")
    assert "The%20Lord%20of%20the%20Rings" in url
    assert "%26" in url  # ampersand encoded


def test_genre_chips_html_caps_at_three():
    """Cards show at most three genre chips regardless of input length."""
    html = genre_chips_html(["Action", "Drama", "Comedy", "Sci-Fi", "Horror"])
    assert html.count("<span") == 3


def test_genre_chips_html_empty_returns_empty_string():
    assert genre_chips_html([]) == ""


def test_provider_logos_empty_returns_empty_string():
    assert provider_logos_html(None) == ""
    assert provider_logos_html([]) == ""


def test_provider_logos_caps_at_four():
    providers = [{"logo": f"L{i}", "name": f"P{i}"} for i in range(10)]
    html = provider_logos_html(providers)
    assert html.count("<img") == 4


def test_poster_html_shows_hot_badge_when_flagged():
    hot = poster_html("url", 8.5, is_hot=True)
    cold = poster_html("url", 8.5, is_hot=False)
    assert "🔥 HOT" in hot
    assert "🔥 HOT" not in cold


def test_poster_html_year_tag_appears_only_when_year_given():
    with_year = poster_html("url", 7.0, year=1999)
    without_year = poster_html("url", 7.0)
    assert "1999" in with_year
    assert "position:absolute;top:8px;right:8px" not in without_year
