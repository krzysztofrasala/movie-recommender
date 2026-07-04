"""Keyword-driven natural-language search parsing (zero API cost).

Turns free text like "scary movie from the 90s" into TMDB discover
parameters: genres, year range, minimum rating and sort order.
"""

from __future__ import annotations

import datetime
import re

# Keyword (or phrase) → TMDB genre id.
GENRE_KEYWORDS = {
    "comedy": 35, "funny": 35, "laugh": 35, "humor": 35, "humour": 35, "hilarious": 35,
    "horror": 27, "scary": 27, "frightening": 27, "terrifying": 27, "creepy": 27, "spooky": 27,
    "romance": 10749, "romantic": 10749, "love story": 10749,
    "action": 28, "fight": 28, "exciting": 28, "explosive": 28,
    "adventure": 12,
    "sci-fi": 878, "scifi": 878, "science fiction": 878, "space": 878, "futuristic": 878, "aliens": 878,
    "drama": 18, "emotional": 18, "intense": 18,
    "animation": 16, "animated": 16, "cartoon": 16, "anime": 16,
    "thriller": 53, "suspense": 53, "tense": 53,
    "mystery": 9648, "detective": 9648, "whodunit": 9648,
    "family": 10751, "kids": 10751, "children": 10751,
    "fantasy": 14, "magic": 14, "magical": 14, "dragons": 14,
    "crime": 80, "gangster": 80, "mafia": 80, "heist": 80,
    "war": 10752, "military": 10752, "battle": 10752,
    "western": 37, "cowboy": 37, "wild west": 37,
    "history": 36, "historical": 36, "period": 36,
    "music": 10402, "musical": 10402,
    "documentary": 99, "true story": 99,
}

# Keyword → TMDB discover sort order.
SORT_KEYWORDS = {
    "popular": "popularity.desc", "trending": "popularity.desc", "hot": "popularity.desc",
    "top rated": "vote_average.desc", "best": "vote_average.desc", "highest rated": "vote_average.desc",
    "newest": "primary_release_date.desc", "recent": "primary_release_date.desc", "latest": "primary_release_date.desc",
    "oldest": "primary_release_date.asc",
}

# Keyword → minimum TMDB vote average.
RATING_KEYWORDS = {
    "masterpiece": 8.5, "excellent": 8.0, "great": 7.5, "good": 7.0, "decent": 6.5,
}


def parse_natural_query(text: str) -> dict:
    """Extract TMDB discover filters from a free-text description."""
    q = text.lower()
    genres: list[int] = []
    vote_gte: float | None = None
    sort_by = "popularity.desc"
    year_gte: int | None = None
    year_lte: int | None = None

    for keyword, genre_id in GENRE_KEYWORDS.items():
        if keyword in q and genre_id not in genres:
            genres.append(genre_id)

    # Decade phrases: "80s", "1990s", "the 90s"
    decade_match = re.search(r"\b(1[0-9]{3}|[0-9]{2})s\b", q)
    if decade_match:
        raw = decade_match.group(1)
        if len(raw) == 2:
            n = int(raw)
            base = 2000 if n <= 20 else 1900
            decade_start = base + (n // 10) * 10
        else:
            decade_start = int(raw) // 10 * 10
        year_gte, year_lte = decade_start, decade_start + 9

    current_year = datetime.date.today().year
    if re.search(r"\b(this year|new releases?|just released)\b", q):
        year_gte = current_year - 1
    elif re.search(r"\bclassic\b", q) and not year_gte:
        year_lte = 2000
        sort_by = "vote_average.desc"
    elif re.search(r"\bvery old\b", q) and not year_gte:
        year_lte = 1980

    for keyword, rating in RATING_KEYWORDS.items():
        if keyword in q:
            vote_gte = max(vote_gte or 0, rating)

    for keyword, sort in SORT_KEYWORDS.items():
        if keyword in q:
            sort_by = sort
            break

    return {
        "genres": genres[:2],
        "year_gte": year_gte,
        "year_lte": year_lte,
        "vote_gte": vote_gte,
        "sort_by": sort_by,
    }
