"""Tests for the natural-language query parser."""

from __future__ import annotations

import datetime

import pytest

from cinescope.nl_query import GENRE_KEYWORDS, parse_natural_query

# TMDB genre ids used across the assertions below.
COMEDY = 35
HORROR = 27
ROMANCE = 10749
SCIFI = 878
ANIMATION = 16
FAMILY = 10751


def test_empty_query_returns_neutral_defaults():
    """Blank input should not invent genres, years or rating floors."""
    result = parse_natural_query("")
    assert result == {
        "genres": [],
        "year_gte": None,
        "year_lte": None,
        "vote_gte": None,
        "sort_by": "popularity.desc",
    }


def test_single_genre_keyword():
    assert parse_natural_query("horror movie")["genres"] == [HORROR]


def test_synonym_maps_to_same_genre():
    """'Scary' and 'horror' are different words with the same TMDB id."""
    assert parse_natural_query("scary movie")["genres"] == [HORROR]
    assert parse_natural_query("scifi film")["genres"] == [SCIFI]


def test_multi_word_keyword_matches():
    """Two-word phrases like 'science fiction' must be detected."""
    assert SCIFI in parse_natural_query("science fiction adventure")["genres"]


def test_multiple_genres_are_deduped_and_capped_at_two():
    """Overloaded queries only keep the first two distinct genres."""
    result = parse_natural_query("funny romantic scary sci-fi thriller")
    assert len(result["genres"]) == 2
    assert len(set(result["genres"])) == 2


def test_two_digit_decade_after_2000():
    """'80s' is 1980s, '10s' is 2010s — parser must disambiguate."""
    assert parse_natural_query("movies from the 80s")["year_gte"] == 1980
    assert parse_natural_query("movies from the 80s")["year_lte"] == 1989
    assert parse_natural_query("movies from the 10s")["year_gte"] == 2010


def test_four_digit_decade():
    assert parse_natural_query("1990s classics")["year_gte"] == 1990
    assert parse_natural_query("1990s classics")["year_lte"] == 1999


def test_this_year_uses_current_year_minus_one_lower_bound():
    """New-release queries should include titles from the last ~year."""
    result = parse_natural_query("new releases")
    assert result["year_gte"] == datetime.date.today().year - 1


def test_classic_keyword_caps_year_and_switches_to_rating_sort():
    """'Classic' means old + highly rated, not just popular."""
    result = parse_natural_query("classic movies")
    assert result["year_lte"] == 2000
    assert result["sort_by"] == "vote_average.desc"


def test_decade_takes_precedence_over_classic():
    """An explicit decade must beat the loose 'classic' cap."""
    result = parse_natural_query("classic 90s movies")
    assert result["year_gte"] == 1990
    assert result["year_lte"] == 1999


def test_rating_keyword_sets_vote_floor():
    assert parse_natural_query("great sci-fi")["vote_gte"] == 7.5
    assert parse_natural_query("masterpiece thriller")["vote_gte"] == 8.5


def test_multiple_rating_keywords_take_the_highest():
    """Conflicting quality words should not lower the bar."""
    assert parse_natural_query("good but excellent")["vote_gte"] == 8.0


def test_sort_keyword_overrides_default():
    assert parse_natural_query("newest sci-fi")["sort_by"] == "primary_release_date.desc"
    assert parse_natural_query("top rated horror")["sort_by"] == "vote_average.desc"


def test_case_insensitivity():
    """Users type however they type — case must not matter."""
    lower = parse_natural_query("horror movie from the 90s")
    upper = parse_natural_query("HORROR MOVIE FROM THE 90S")
    assert lower == upper


def test_combined_query():
    """Realistic combined query should yield all detected filters."""
    result = parse_natural_query("great scary movie from the 90s")
    assert HORROR in result["genres"]
    assert result["year_gte"] == 1990
    assert result["year_lte"] == 1999
    assert result["vote_gte"] == 7.5


@pytest.mark.parametrize("keyword,expected_id", [
    ("funny", COMEDY),
    ("romantic", ROMANCE),
    ("cartoon", ANIMATION),
    ("kids", FAMILY),
])
def test_common_synonyms(keyword: str, expected_id: int):
    assert parse_natural_query(f"{keyword} movie")["genres"] == [expected_id]


def test_all_genre_keywords_are_lowercase():
    """Parser lowercases input, so keyword table must match."""
    for keyword in GENRE_KEYWORDS:
        assert keyword == keyword.lower(), f"non-lowercase key: {keyword!r}"
